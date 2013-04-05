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
from pydhcplib.type_hwmac import hwmac

from pyping import Ping

from ..nodes.models import Node


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
        self.broadcast = str(ipv4([255,255,255,255]))

        self.logger.info('DHCP listen on %s(%s)', self.listen_on_ip, self.listen_on_iface)

    def CreateSocket(self):
        DhcpServer.CreateSocket(self)
        self.dhcp_socket.setsockopt(socket.SOL_SOCKET, IN.SO_BINDTODEVICE, self.listen_on_iface)


    def _client_id2str(self, id):
        if id:
            return str().join( chr( val ) for val in id )


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
        return Ping(str(ip), timeout=5000).do()


    def HandleDhcpAll(self, packet):
        packet.str_mac = str(hwmac(packet.GetHardwareAddress()))
        packet.str_client_identifier = str().join( chr( val ) for val in packet.GetClientIdentifier() )


    def HandleDhcpDiscover(self, packet):
        self.logger.info('DISCOVER from %s', packet.str_mac)
        self.logger.debug(packet.str())

        node = Node.query.get(packet.str_client_identifier or packet.str_mac)

        if node is None:
            if packet.str_client_identifier:
                self.logger.info('Node with client identifier "%s" has not listen in database', packet.str_client_identifier)
            else:
                self.logger.info('Node %s has not listen in database', packet.str_mac)
            return

        offer = DhcpPacket()
        offer.CreateDhcpOfferPacketFrom(packet)
        yiaddr = node.offer(self.icmp_test_alive)

        offer.SetOption('ip_address_lease_time', self._long2list(node.pool.lease_time)) # wrong!
        offer.SetOption("yiaddr", yiaddr.words)
        offer.SetOption("siaddr", self.listen_on_ip.list())

        self.logger.debug(offer.str())

        if self.SendDhcpPacketTo(offer, self.broadcast, self.emit_port) <= 0:
            self.logger.error('Could not send DHCP offer to %s', packet.str_mac)


    def nack(self, packet):
        packet.TransformToDhcpNackPacket()
        if self.SendDhcpPacketTo(packet, self.broadcast, self.emit_port) <= 0:
            self.logger.error('Could not send DHCP NACK to %s', packet.str_mac)


    def HandleDhcpRequest(self, packet):

        self.logger.info('REQUEST from %s', packet.str_mac)
        self.logger.debug(packet.str())

        node = Node.query.get(packet.str_client_identifier or packet.str_mac)

        if packet.GetOption('server_identifier'):
            server_ip = ipv4(self._list2long(packet.GetOption('server_identifier')))
            if server_ip != self.listen_on_ip:
                self.logger.info('Node %s has accept offer from another server', packet.str_mac)
                node.cleanup_offers(packet.str_client_identifier or packet.str_mac)
                return

        renew_ip = self._list2long(packet.GetOption("ciaddr"))
        new_ip = self._list2long(packet.GetOption('request_ip_address'))

        request_ip_address = renew_ip or new_ip

        if not request_ip_address:
            self.logger.error('Got DHCP REQUEST from %s with empty request_ip_address and ciaddr', packet.str_mac)
            self.nack(packet)
            return


        lease = node.lease(request_ip_address, existen=renew_ip)

        if not lease:
            self.logger.info('Address %s requested by %s is not found in offers store', str(ipv4(request_ip_address)), packet.str_mac)
            self.nack(packet)
            return

        ack = DhcpPacket()
        ack.CreateDhcpAckPacketFrom(packet)
        ack.SetOption('ip_address_lease_time', self._long2list(node.pool.lease_time))
        ack.SetOption("yiaddr", lease.yiaddr.words)
        ack.SetOption("broadcast_address", list(node.pool.subnet.broadcast.words))
        ack.SetOption("time_offset", self._long2list(node.pool.time_offset))
        ack.SetOption("siaddr", self.listen_on_ip.list())
        ack.SetOption("domain_name", strlist(str(node.pool.domain)).list())
        ack.SetOption("router", list(node.pool.router.words))
        ack.SetOption("host_name", strlist(str(node.hostname)).list())

        if node.pool.domain_name_servers:
            name_servers = [ip.words for ip in node.pool.domain_name_servers]
            ack.SetOption("domain_name_server", list(reduce(lambda x,y: x+y,name_servers)))

        if node.pool.ntp_servers:
            ntp_servers = [ip.words for ip in node.pool.ntp_servers]
            ack.SetOption("ntp_servers", list(reduce(lambda x,y: x+y,ntp_servers)))

        node.commit_lease(lease)

        self.logger.debug(ack.str())
        if self.SendDhcpPacketTo(ack, self.broadcast, self.emit_port) <= 0:
            self.logger.error('Could not send DHCP ACK to %s', packet.str_mac)



    def HandleDhcpDecline(self, packet):
        self.logger.warning('DECLINE from %s for ip %s', self._hw_addr2str(packet.GetHardwareAddress()), packet.getOption('ciaddr'))
        self.logger.debug(packet.str())

        decline_ip = self._list2long(packet.GetOption('request_ip_address'))

        node = Node.query.get(packet.str_client_identifier or packet.str_mac)
        if node:
            node.decline(decline_ip)


    def HandleDhcpRelease(self, packet):
        self.logger.info('RELEASE from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        self.logger.debug(packet.str())

        node = Node.query.get(packet.str_client_identifier or packet.str_mac)
        node.release()


    def HandleDhcpInform(self, packet):
        self.logger.info('INFORM from %s', packet.str_mac)
        self.logger.debug(packet.str())


def init(reactor, config):
    dhcp_listen_on = config.get('DHCP_LISTEN', [])

    def worker_wrapper(w):
        while True:
            w()

    for iface in dhcp_listen_on:
        worker = PyBootstapperDhcpWorker(config, iface + '\0').GetNextDhcpPacket
        reactor.callFromThread(worker_wrapper, worker)
