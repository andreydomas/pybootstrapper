import logging

from twisted.internet import reactor

from pydhcplib.dhcp_packet import *
from pydhcplib.dhcp_network import *
from pydhcplib.type_strlist import strlist
from pydhcplib.type_ipv4 import ipv4

from ..nodes.models import Node
from models import Lease

logger = logging.getLogger('dhcp')

class Server(DhcpServer):
    def __init__(self, config):

        self.client_port = config.get('DHCP_CLIENT_LISTEN_PORT', 68)
        self.server_port = config.get('DHCP_SERVER_LISTEN_PORT', 67)
        self.listen_on = config.get('DHCP_LISTEN_ADDRESS', '0.0.0.0')

        DhcpServer.__init__(self,
                            self.listen_on,
                            self.client_port,
                            self.server_port
                            )


    def _hw_addr2str(self, hw):
        return ':'.join(map(lambda x: str(hex(x))[2:], hw))

    def _str2ipv4(self, s):
        return ipv4(str(s)).list()


    def HandleDhcpDiscover(self, packet):
        logger.info('DISCOVER from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        logger.debug(packet.str())

        node = Node.by_mac(self._hw_addr2str(packet.GetHardwareAddress()))

        if node is None:
            logger.info('Node %s has not listen in database', self._hw_addr2str(packet.GetHardwareAddress()))
            return

        offer = DhcpPacket()
        offer.CreateDhcpOfferPacketFrom(packet)

        if node.static_ip:
            offer.SetOption("yiaddr", self._str2ipv4(node.static_ip))

        offer.SetOption("domain_name", strlist(str(node.pool.domain)).list())
        offer.SetOption("router", self._str2ipv4(node.pool.router))

        if self.SendDhcpPacketTo(offer, str(ipv4(offer.GetGiaddr())), self.client_port) <= 0:
            logger.error('Could not send DHCP offer to %s', self._hw_addr2str(offer.GetHardwareAddress()))


    def HandleDhcpRequest(self, packet):
        logger.info('REQUEST from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        logger.debug(packet.str())

        ack = DhcpPacket()
        ack.CreateDhcpAckPacketFrom(packet)

        if self.SendDhcpPacketTo(ack, '.'.join(map(str,ack.GetGiaddr())), self.client_port) <= 0:
            logger.error('Could not send DHCP ACK to %s', self._hw_addr2str(offer.GetHardwareAddress()))


    def HandleDhcpDecline(self, packet):
        logger.warning('DECLINE from %s for ip %s', self._hw_addr2str(packet.GetHardwareAddress()), packet.getOption('ciaddr'))
        logger.debug(packet.str())


    def HandleDhcpRelease(self, packet):
        logger.info('RELEASE from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        logger.debug(packet.str())


    def HandleDhcpInform(self, packet):
        logger.info('INFORM from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        logger.debug(packet.str())

def init(config):
    return Server(config).GetNextDhcpPacket
