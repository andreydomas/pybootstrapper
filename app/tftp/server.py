import threading
import socket
import binascii
import os
import select
import struct

IMAEGE_PREFIX = 'images/'
KERNEL_PREFIX = 'kernels/'

class TIDException(Exception):
    def __init__(self, code):
        self.code = code


class TID(object):
    def __init__(self, message, config):
        message = message.split('\x00')
        self.filename = message[0][1:]

        if self.filename == 'gpxelinux.0':
            self._data = self._regular_file(config.get('GPXELINUX'))
            self.tsize = os.stat(config.get('GPXELINUX')).st_size

        else:
            raise TIDException(1)

        self.blksize = config.get('TFTP_DEFAULT_BLKSIZE', 1456)

        for i, field in enumerate(message[1:]):
            if field == 'blksize':
                client_blksize = int(message[1:][i+1])
                if client_blksize:
                    self.blksize = client_blksize

        if self.blksize < 8 or self.blksize > 65464 or self.blksize*65535 < self.tsize:
            raise TIDException(0)


    def _regular_file(self, fname):
        if not os.path.isfile(fname):
            raise TIDException(1)

        try:
            return open(fname, 'r')
        except IOError:
            raise TIDException(2)

    def data(self, block):
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


    def _oack(self, options, address):
        self.app.logger.debug('OACK %s to %s', str(options), address[0])

        oack_pkg = struct.pack('>H', 6) # Opcode(6 == Option Acknowledgment)
        for opt, value in options.iteritems():
            oack_pkg += struct.pack('>%ss' % len(str(opt)), str(opt) ) + '\x00'
            oack_pkg += struct.pack('>%ss' % len(str(value)), str(value)) + '\x00'

        self.socket.sendto(oack_pkg, address)


    def _rrq(self, message, address):
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

        return self._oack({
                        'blksize': tid.blksize,
                        'tsize': tid.tsize,
                    }, address)


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

        self.app.logger.error('ERROR to %s: %s', address[0], msg)

        self.socket.sendto(
                    struct.pack('>H', 5) # Opcode(5 == Error)
                  + struct.pack('>H', code) # ErrorCode
                  + struct.pack('>%ss' % len(msg), msg) + '\x00' # ErrMsg
                  , address)

    def _data(self, block, address, data):
        self.socket.sendto(
                  struct.pack('>H', 3) # Opcode(3 == DATA)
                + struct.pack('>H', block) # Block #
                + data(block)
                , address)


    def _ack(self, message, address):
        _block = [ ( '\x00' if x == '' else x ) for x in message[1:] ]
        block=struct.unpack('>H', ''.join(_block))[0]
        #self.app.logger.debug('ACK from %s for block #%s', address[0], block)

        try:
            tid = self.tids[address]
        except KeyError:
            self._error(5, address)

        next_block = int(block)+1
        self._data(next_block, address, tid.data)


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
