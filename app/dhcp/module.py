import logging
import struct
import fcntl
import socket
import IN

from twisted.internet.task import LoopingCall, deferLater

from pydhcplib.dhcp_packet import DhcpPacket
from pydhcplib.dhcp_network import DhcpServer
from pydhcplib.type_strlist import strlist
from pydhcplib.type_ipv4 import ipv4

from ..nodes.models import Node, Pool, Lease


class PyBootstapperDhcpWorker(DhcpServer):
    def __init__(self, config, listen_on_iface):

        self.listen_on_iface = listen_on_iface
        self.logger = logging.getLogger('dhcp')
        self.term_received = False

        DhcpServer.__init__(self)

        listen_on = socket.inet_ntoa(fcntl.ioctl(
                            self.dhcp_socket.fileno(),
                            0x8915,  # SIOCGIFADDR
                            struct.pack('256s', self.listen_on_iface[:15])
                        )[20:24])

        self.listen_on_ip = ipv4(listen_on)

        self.logger.info('DHCP listen on %s(%s)', self.listen_on_ip, self.listen_on_iface)

    def CreateSocket(self):
        DhcpServer.CreateSocket(self)
        self.dhcp_socket.setsockopt(socket.SOL_SOCKET, IN.SO_BINDTODEVICE, self.listen_on_iface)


    def _hw_addr2str(self, hw):
        """
        Convert MAC from list form to common unix form.
        """
        return ':'.join(map(lambda x: str(hex(x))[2:], hw))


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
        return l[3] + l[2]*256 + l[1]*256*256 + l[0]*256*256*256


    def HandleDhcpDiscover(self, packet):
        self.logger.info('DISCOVER from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        self.logger.debug(packet.str())

        node = Node.by_mac(self._hw_addr2str(packet.GetHardwareAddress()))

        if node is None:
            self.logger.info('Node %s has not listen in database', self._hw_addr2str(packet.GetHardwareAddress()))
            return

        offer = DhcpPacket()
        offer.CreateDhcpOfferPacketFrom(packet)

        offer.SetOption('ip_address_lease_time', self._long2list(node.pool.lease_time))

        offer.SetOption("yiaddr", node.make_offer(self._list2long(offer.GetOption('xid'))).words)

        offer.SetOption("siaddr", self.listen_on_ip.list())

        offer.SetOption("domain_name", strlist(str(node.pool.domain)).list())

        offer.SetOption("router", list(node.pool.router.words))

        self.logger.debug(offer.str())

        if self.SendDhcpPacketTo(offer, str(ipv4(offer.GetGiaddr())), self.emit_port) <= 0:
            self.logger.error('Could not send DHCP offer to %s', self._hw_addr2str(offer.GetHardwareAddress()))


    def HandleDhcpRequest(self, packet):
        self.logger.info('REQUEST from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        self.logger.debug(packet.str())

        xid = self._list2long(packet.GetOption('xid'))
        request_ip_address = self._list2long(packet.GetOption('request_ip_address'))
        mac = self._list2long(packet.GetOption('chaddr'))

        offer = Lease.check_offer(mac, xid, request_ip_address)
        if not offer:
            self.logger.info('Node %s has accepted offer from another server', self._hw_addr2str(packet.GetHardwareAddress()))
            return

        ack = DhcpPacket()
        ack.CreateDhcpAckPacketFrom(packet)

        if self.SendDhcpPacketTo(ack, '.'.join(map(str,ack.GetGiaddr())), self.emit_port) <= 0:
            self.logger.error('Could not send DHCP ACK to %s', self._hw_addr2str(offer.GetHardwareAddress()))


    def HandleDhcpDecline(self, packet):
        self.logger.warning('DECLINE from %s for ip %s', self._hw_addr2str(packet.GetHardwareAddress()), packet.getOption('ciaddr'))
        self.logger.debug(packet.str())


    def HandleDhcpRelease(self, packet):
        self.logger.info('RELEASE from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        self.logger.debug(packet.str())


    def HandleDhcpInform(self, packet):
        self.logger.info('INFORM from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        self.logger.debug(packet.str())


def init(reactor, config):
    dhcp_listen_on = config.get('DHCP_LISTEN', [])

    def worker_wrapper(w):
        while True:
            w()

    for iface in dhcp_listen_on:
        worker = PyBootstapperDhcpWorker(config, iface + '\0').GetNextDhcpPacket
        reactor.callFromThread(worker_wrapper, worker)
