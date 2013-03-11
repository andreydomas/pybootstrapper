import logging

from twisted.internet import reactor

from pydhcplib.dhcp_packet import *
from pydhcplib.dhcp_network import *
from pydhcplib.type_strlist import strlist
from pydhcplib.type_ipv4 import ipv4

from ..nodes.models import Node

logger = logging.getLogger('dhcp')

class Server(DhcpServer):
    def __init__(self, config, listen_on):

        self.client_port = config.get('DHCP_CLIENT_LISTEN_PORT', 68)
        self.server_port = config.get('DHCP_SERVER_LISTEN_PORT', 67)
        self.listen_on = ipv4(listen_on)

        DhcpServer.__init__(self,
                            '0.0.0.0',
                            self.client_port,
                            self.server_port
                            )


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
        logger.info('DISCOVER from %s', self._hw_addr2str(packet.GetHardwareAddress()))
        logger.debug(packet.str())

        node = Node.by_mac(self._hw_addr2str(packet.GetHardwareAddress()))

        if node is None:
            logger.info('Node %s has not listen in database', self._hw_addr2str(packet.GetHardwareAddress()))
            return

        offer = DhcpPacket()
        offer.CreateDhcpOfferPacketFrom(packet)

        offer.SetOption('ip_address_lease_time', self._long2list(node.pool.lease_time))

        offer.SetOption("yiaddr",
                node.pool.make_offer(node,
                    self._list2long(offer.GetOption('xid')),
                    self.listen_on.int()
                ).words
            )

        offer.SetOption("siaddr", self.listen_on.list())

        offer.SetOption("domain_name", strlist(str(node.pool.domain)).list())

        offer.SetOption("router", list(node.pool.router.words))

        logger.debug(offer.str())

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
    dhcp_listen_on = config.get('DHCP_LISTEN', ['0.0.0.0'])

    servers = []

    for addr in dhcp_listen_on:
        servers.append(Server(config, addr))

    def get_next_packet():
        for server in servers:
            server.GetNextDhcpPacket()

    return get_next_packet
