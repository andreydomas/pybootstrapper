import threading
import logging
import struct
import fcntl
import socket
import IN

from functools import wraps
from pydhcplib.dhcp_packet import DhcpPacket
from pydhcplib.dhcp_network import DhcpServer
from pydhcplib.type_strlist import strlist
from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_hwmac import hwmac

from pyping import Ping

from ..nodes.models import Node
from ..flask_ctx import flask_context_push, flask_context_pop


class PyBootstapperDhcpWorker(DhcpServer, threading.Thread):

    def __init__(self, app, listen_on_iface):

        self.app = app

        self.listen_on_iface = listen_on_iface
        self.kill = False


        DhcpServer.__init__(self)
        threading.Thread.__init__(self)

        listen_on = socket.inet_ntoa(fcntl.ioctl(
                            self.dhcp_socket.fileno(),
                            0x8915,  # SIOCGIFADDR
                            struct.pack('256s', self.listen_on_iface[:15])
                        )[20:24])

        self.listen_on_ip = ipv4(listen_on)
        self.broadcast = str(ipv4([255,255,255,255]))

        self.app.logger.info('DHCP listen on %s(%s)', self.listen_on_ip, self.listen_on_iface)


    def CreateSocket(self):
        DhcpServer.CreateSocket(self)
        self.dhcp_socket.setsockopt(socket.SOL_SOCKET, IN.SO_BINDTODEVICE, self.listen_on_iface)


    def _long2list(self, l):
        """
        Convert long to list of octets.
        """
        q = [l >> 24 & 0xFF]
        q.append(l >> 16 & 0xFF)
        q.append(l >> 8 & 0xFF)
        q.append(l & 0xFF)
        return q


    def _list2long(self, l):
        """
        Convert list of octets to long.
        """
        if l:
            return l[3] + l[2]*256 + l[1]*256*256 + l[0]*256*256*256


    def icmp_test_alive(self, ip):
        return Ping(str(ip), timeout=self.app.config.get('DHCP_TEST_TIMEOUT', 500)).do()


    @flask_context_push
    def HandleDhcpAll(self, packet):
        packet.str_mac = str(hwmac(packet.GetHardwareAddress()))
        packet.str_client_identifier = str().join( chr( val ) for val in packet.GetClientIdentifier() )
        packet.str_user_class = str().join( chr( val ) for val in packet.GetOption('user_class') )


    @flask_context_pop
    def HandleDhcpDiscover(self, packet):
        self.app.logger.info('DISCOVER from %s', packet.str_mac)
        self.app.logger.debug(packet.str())

        node = Node.query.get(packet.str_mac)

        if node is None:
            self.app.logger.info('Node %s has not listen in database', packet.str_mac)
            return

        offer = DhcpPacket()
        offer.CreateDhcpOfferPacketFrom(packet)
        yiaddr = node.offer(self.icmp_test_alive)

        if packet.str_user_class == 'gPXE':
            options = node.gpxe_options
        else:
            options = node.pxe_options

        for opt in options:
            offer.SetOption(opt.option, opt.binary)

        offer.SetOption("yiaddr", yiaddr.words)
        offer.SetOption("siaddr", self.listen_on_ip.list())

        self.app.logger.debug(offer.str())

        if self.SendDhcpPacketTo(offer, self.broadcast, self.emit_port) <= 0:
            self.app.logger.error('Could not send DHCP offer to %s', packet.str_mac)


    def nack(self, packet):
        packet.TransformToDhcpNackPacket()
        if self.SendDhcpPacketTo(packet, self.broadcast, self.emit_port) <= 0:
            self.app.logger.error('Could not send DHCP NACK to %s', packet.str_mac)


    @flask_context_pop
    def HandleDhcpRequest(self, packet):

        self.app.logger.info('REQUEST from %s', packet.str_mac)
        self.app.logger.debug(packet.str())

        node = Node.query.get(packet.str_mac)

        renew_ip = self._list2long(packet.GetOption("ciaddr"))
        new_ip = self._list2long(packet.GetOption('request_ip_address'))

        server_id = ipv4(self._list2long(packet.GetOption('server_identifier')))

        lease = None

        if server_id.int() == 0:  # INIT-REBOOT
            lease = node.lease(new_ip)

        elif server_id == self.listen_on_ip:  # SELECT
            request_ip_address = renew_ip or new_ip
            if not request_ip_address:
                self.app.logger.error('Got DHCP REQUEST from %s with empty request_ip_address and ciaddr', packet.str_mac)
            else:
                lease = node.lease(request_ip_address, existen=renew_ip)

        else:
            self.app.logger.info('Node %s has accept offer from another server', packet.str_mac)
            node.cleanup_offers()
            return

        if not lease:
            self.nack(packet)
            return

        ack = DhcpPacket()
        ack.CreateDhcpAckPacketFrom(packet)

        if packet.str_user_class in ['gPXE', 'iPXE']:
            options = node.gpxe_options
        else:
            options = node.pxe_options

        for opt in options:
            ack.SetOption(opt.option, opt.binary)

        ack.SetOption("yiaddr", lease.yiaddr.words)
        ack.SetOption("siaddr", self.listen_on_ip.list())

        node.commit_lease(lease)

        self.app.logger.debug(ack.str())
        if self.SendDhcpPacketTo(ack, self.broadcast, self.emit_port) <= 0:
            self.app.logger.error('Could not send DHCP ACK to %s', packet.str_mac)


    @flask_context_pop
    def HandleDhcpDecline(self, packet):
        self.app.logger.warning('DECLINE from %s for ip %s', packet.str_mac, packet.getOption('ciaddr'))
        self.app.logger.debug(packet.str())

        decline_ip = self._list2long(packet.GetOption('request_ip_address'))

        node = Node.query.get(packet.str_mac)
        if node:
            node.decline(decline_ip)


    @flask_context_pop
    def HandleDhcpRelease(self, packet):
        self.app.logger.info('RELEASE from %s', packet.str_mac)
        self.app.logger.debug(packet.str())

        node = Node.query.get(packet.str_mac)
        node.release()


    @flask_context_pop
    def HandleDhcpInform(self, packet):
        self.app.logger.info('INFORM from %s', packet.str_mac)
        self.app.logger.debug(packet.str())


    def run(self):
        while not self.kill:
            self.GetNextDhcpPacket(1)


def init(create_app):

    app = create_app()

    dhcp_listen_on = app.config.get('DHCP_LISTEN', [])

    threads = []

    for iface in dhcp_listen_on:
        worker = PyBootstapperDhcpWorker(app, iface + '\0')
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
