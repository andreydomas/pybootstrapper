import re
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from netaddr import *

from app import db, app
from ..models import Fixtured
from ..sqla_types import *

class Pool(Fixtured, db.Model):
    __tablename__ = 'pools'
    created = db.Column(db.DateTime, nullable=False, default=datetime.now())
    subnet = db.Column(Subnet(18), primary_key=True)
    router = db.Column(Ip, nullable=True)
    domain = db.Column(db.String(255), nullable=False)
    time_offset = db.Column(db.Integer, nullable=False, default=0) # offset from UTC
    lease_time = db.Column(db.Integer, nullable=False, default=86400)

    domain_name_servers_str = db.Column('domain_name_servers', db.String(255), nullable=True)
    @hybrid_property
    def domain_name_servers(self):
        if self.domain_name_servers_str:
            return [ IPAddress(x.strip(' ')) for x in self.domain_name_servers_str.split(',') ]

    ntp_servers_str = db.Column('ntp_servers', db.String(255), nullable=True)
    @hybrid_property
    def ntp_servers(self):
        if self.ntp_servers_str:
            return [ IPAddress(x.strip(' ')) for x in self.ntp_servers_str.split(',') ]

    @property
    def leases(self):
        return db.object_session(self).query(Lease).filter(Lease.node_mac==Node.mac, Node.pool_subnet==self.subnet).all()


class Node(Fixtured, db.Model):
    __tablename__ = 'nodes'
    mac = db.Column(Mac, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now())
    hostname = db.Column(db.String(255), nullable=False)
    static_ip = db.Column(Ip, nullable=True)
    pool_subnet = db.Column(Subnet(18), db.ForeignKey(Pool.subnet), nullable=False)

    @declared_attr
    def pool(cls):
        return db.relationship(Pool, lazy='joined', innerjoin=True,
                  primaryjoin=db.and_(cls.pool_subnet==Pool.subnet),
                  backref=db.backref('nodes', lazy='select', order_by=cls.created.desc()))

    @classmethod
    def by_mac(cls, mac):
        return cls.query.filter(cls.mac == mac).first()

    @classmethod
    def cleanup_offers_for_mac(cls, mac):
        Lease.query.filter(Lease.node_mac==mac, Lease.leasing_until==None).delete()
        db.session.commit()

    def make_offer(self):

        offer_timeout = datetime.now() - timedelta(seconds=app.config.get('DHCP_OFFER_TIMEOUT', 15))
        Lease.query \
             .filter(Lease.leasing_until==None) \
             .filter(Lease.created < offer_timeout ) \
             .delete()

        existen_leasing = Lease.query.with_parent(self).filter(Lease.leasing_until!=None).first()

        if existen_leasing:
            return existen_leasing.yiaddr

        ip = self.static_ip
        if not ip:
            ip = self.pool.subnet.ip + 1
            leasing_ip_list = [ lease.yiaddr for lease in self.pool.leases ]
            while ip <= self.pool.subnet.ip + self.pool.subnet.size:
                if not ip in leasing_ip_list:
                    break
                ip += 1

        lease = Lease(self.mac, ip)
        db.session.add(lease)
        db.session.commit()

        return ip

    def make_lease(self, ip):
        return Lease.query.filter(Lease.node_mac==self.mac, Lease.yiaddr==ip).first()

class Lease(db.Model):
    __tablename__ = 'leasing'
    created = created = db.Column(db.DateTime, default=datetime.now())
    node_mac = db.Column(Mac, db.ForeignKey(Node.mac), primary_key=True)
    yiaddr = db.Column(Ip, primary_key=True)
    leasing_until = db.Column(db.DateTime, nullable=True) # null mean offered


    def __init__(self, mac, yiaddr):
        self.node_mac = mac
        self.yiaddr = yiaddr

    @declared_attr
    def node(cls):
        return db.relationship(Node, lazy='select', innerjoin=True,
               backref=db.backref('leases', lazy='select', order_by=cls.created.desc()))

    @property
    def pool(self):
        return db.object_session(self).query(Pool).filter(Pool.subnet==Node.pool_subnet, Node.mac==self.node_mac).first()

    def commit_leasing(self):
        self.leasing_until = datetime.now() + timedelta(seconds=self.pool.lease_time)
        db.session.commit()
