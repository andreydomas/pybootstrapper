import re
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from ..models import Fixtured
from ..sqla_types import *

class Pool(Fixtured, db.Model):
    __tablename__ = 'pools'
    created = db.Column(db.DateTime, nullable=False, default=datetime.now())
    subnet = db.Column(Subnet(18), primary_key=True)
    router = db.Column(Ip, nullable=True)
    domain = db.Column(db.String(255), nullable=False)
    lease_time = db.Column(db.Integer, nullable=False, default=86400)


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

    def make_offer(self, xid):
        existen_leasing = Lease.query.with_parent(self).filter(Lease.xid == xid) \
                                     .filter(Lease.leasing_due == None) \
                                     .first()

        if existen_leasing:
            return existen_leasing.yiaddr

        ip = self.static_ip
        if not ip:
            ip = self.pool.subnet.ip + 1
            leasing_ip_list = [ leased.yiaddr for leased in self.pool.leases.all() ]
            while ip <= self.pool.subnet.ip + self.pool.subnet.size:
                if not ip in leasing_ip_list:
                    break
                ip += 1

        lease = Lease()
        lease.xid = xid
        lease.pool = self.pool
        lease.yiaddr = ip
        self.leases.append(lease)
        db.object_session(self).commit()
        return ip

    def check_offer(self, xid, request_ip_address):
        return Lease.query.with_parent(self).filter(Lease.xid == xid) \
                                            .filter(Lease.leasing_due == None) \
                                            .filter(Lease.yiaddr == request_ip_address) \
                                            .first()



class Lease(db.Model):
    __tablename__ = 'leasing'
    created = created = db.Column(db.DateTime, default=datetime.now())
    xid = db.Column(db.Integer, primary_key=True)
    pool_subnet = db.Column(Subnet(18), db.ForeignKey(Pool.subnet), nullable=False)
    node_mac = db.Column(Mac, db.ForeignKey(Node.mac), primary_key=True)
    yiaddr = db.Column(Ip, nullable=True)
    leasing_due = db.Column(db.DateTime, nullable=True)

    @declared_attr
    def node(cls):
        return db.relationship(Node, lazy='select', innerjoin=True,
               backref=db.backref('leases', lazy='select', order_by=cls.created.desc()))

    @declared_attr
    def pool(cls):
        return db.relationship(Pool, lazy='select',
                     backref=db.backref('leases', lazy='dynamic', order_by=cls.created.desc()),
                )

    @classmethod
    def check_offer(cls, mac, xid, request_ip_address):
        return cls.query.filter(cls.xid == xid) \
                        .filter(cls.node_mac == mac) \
                        .filter(cls.leasing_due == None) \
                        .filter(cls.yiaddr == request_ip_address) \
                        .first()

