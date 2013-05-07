import threading
import socket
import binascii
import os
import select
import struct
from sqlalchemy.exc import StatementError

from ..flask_ctx import flask_context_push, flask_context_pop
from ..nodes.models import Node

IMAEGE_PREFIX = 'images/'
KERNEL_PREFIX = 'kernels/'
MAX_TFTP_BLKSIZE = 4096


class PXELinuxConfig(object):
    def __init__(self, farm):
        self.image = farm.boot_images[0]

        self.kernel = self.image.kernel
        self.kernel_opts = self.image.kernel_opts or ''

    def __str__(self):
        return 'DEFAULT %(kernel)s\n' \
               'APPEND %(append)s\n' % {

                    'kernel': KERNEL_PREFIX + self.kernel.name,

                    'append': 'initrd=%s %s' % (
                                    '%s%d/%s' % (IMAEGE_PREFIX, self.image.farm_id, self.image.filename),
                                    self.kernel_opts
                                )

                }


class TIDException(Exception):
    def __init__(self, code):
        self.code = code


class TID(object):
    def __init__(self, message, config):
        message = message.split('\x00')
        self.filename = message[0][1:]

        self.blksize = 512
        for i, field in enumerate(message[1:]):
            if field == 'blksize':
                self.blksize = int(message[1:][i+1])

        if self.blksize > MAX_TFTP_BLKSIZE:
            self.blksize = MAX_TFTP_BLKSIZE

        if self.filename == 'pxelinux.0':
            self._data = self._regular_file(config.get('PXELINUX'))

        elif self.filename.startswith(KERNEL_PREFIX):
            kernel_name = config.get('KERNELS_STORE') + '/' + self.filename.split(KERNEL_PREFIX)[1]
            self._data = self._regular_file(kernel_name)

        elif self.filename.startswith(IMAEGE_PREFIX):
            image_name = config.get('IMAGES_STORE') + '/' + self.filename.split(IMAEGE_PREFIX)[1]
            self._data = self._regular_file(image_name)

        elif self.filename.startswith('pxelinux.cfg/01-'):
            self._data = self._pxelinux_cfg(self.filename.split('pxelinux.cfg/01-')[1])

        else:
            raise TIDException(1)


    def _regular_file(self, fname):
        if not os.path.isfile(fname):
            raise TIDException(1)

        try:
            return open(fname, 'r')
        except IOError:
            raise TIDException(2)

    def _pxelinux_cfg(self, mac):
        try:
            node = Node.query.get(mac)
        except StatementError:
            return
        except IndexError:
            return

        if node:
            return PXELinuxConfig(node.pool.farm)

    def data(self, block):
        if isinstance(self._data, PXELinuxConfig):
            return str(self._data)[(block-1)*self.blksize:self.blksize*block]
        else:
            self._data.seek((block-1)*self.blksize)
            return self._data.read(self.blksize)


class PyBootstapperTftpWorker(threading.Thread):
    def __init__(self, app, listen_on):
        self.kill = False
        self.app = app
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1)
        self.socket.bind((listen_on, 69))
        threading.Thread.__init__(self)
        self.tids = {}


    @flask_context_pop
    def _oack(self, options, address):
        self.app.logger.debug('OACK %s to %s', str(options), address[0])

        oack_pkg = struct.pack('>H', 6) # Opcode(6 == Option Acknowledgment)
        for opt, value in options.iteritems():
            oack_pkg += struct.pack('>%ss' % len(str(opt)), str(opt) ) + '\x00'
            oack_pkg += struct.pack('>%ss' % len(str(value)), str(value)) + '\x00'

        self.socket.sendto(oack_pkg, address)


    def _rrq(self, message, address):
        print message
        try:
            tid = TID(message, self.app.config)
        except TIDException, e:
            self._error(e.code, address)
            return

        self.tids[address] = tid
        self.app.logger.debug('RRQ from %s for %s with blksize %d', address[0], repr(tid.filename), tid.blksize)

        # OACK is not needed
        if tid.blksize == 512:
            return self._data(1, address, tid.data)

        return self._oack({'blksize': tid.blksize}, address)


    @flask_context_pop
    def _error(self, code, address):

        msg = {
            0: 'Not defined, see error message (if any).',
            1: 'File not found.',
            2: 'Access violation.',
            3: 'Disk full or allocation exceeded.',
            4: 'Illegal TFTP operation.',
            5: 'Unknown transfer ID.',
            6: 'File already exists.',
            7: 'No such user.'
        }[code]

        self.socket.sendto(
                    struct.pack('>H', 5) # Opcode(5 == Error)
                  + struct.pack('>H', code) # ErrorCode
                  + struct.pack('>%ss' % len(msg), msg) + '\x00' # ErrMsg
                  , address)

    @flask_context_pop
    def _data(self, block, address, data):
        self.socket.sendto(
                  struct.pack('>H', 3) # Opcode(3 == DATA)
                + struct.pack('>H', block) # Block #
                + data(block)
                , address)


    def _ack(self, message, address):
        _block = [ ( '\x00' if x == '' else x ) for x in message[1:] ]
        block=struct.unpack('>H', ''.join(_block))[0]
        self.app.logger.debug('ACK from %s for block #%s', address[0], block)

        try:
            tid = self.tids[address]
        except KeyError:
            self._error(5, address)

        next_block = int(block)+1
        self._data(next_block, address, tid.data)


    @flask_context_push
    def handleTftpMessage(self, message, address):
        if message.startswith(struct.pack('>H', 1)): #RRQ(1)
            self._rrq(message[1:], address)

        elif message.startswith(struct.pack('>H', 4)): #ACK(4)
            self._ack(message[1:], address)

        else:
            self._error(4, address)


    def run(self):
        while not self.kill:
            data_input, data_output, data_except = select.select([self.socket], [], [], 1)
            if data_input:
                message, address = self.socket.recvfrom(8192)
                self.handleTftpMessage(message, address)


def init(create_app):

    app = create_app()

    tftp_listen = app.config.get('TFTP_LISTEN')

    threads = []

    worker = PyBootstapperTftpWorker(app, tftp_listen)
    worker.daemon = True
    threads.append(worker)
    worker.start()

    while len(threads) > 0:
        try:
            threads = [t.join(1) or t for t in threads if t is not None and t.isAlive()]
        except KeyboardInterrupt:
            print "Ctrl-c received! Sending kill to threads..."
            for t in threads:
                t.kill = True
