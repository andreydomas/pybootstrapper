import re
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declared_attr
from netaddr import *

from app import db, app
from ..pools.models import Pool
from ..models import Fixtured
from ..sqla_types import *


class Node(Fixtured, db.Model):
    __tablename__ = 'nodes'
    id = db.Column(db.String, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now())
    hostname = db.Column(db.String(255), nullable=False)
    static_ip = db.Column(Ip, nullable=True)
    pool_subnet = db.Column(Subnet(18), db.ForeignKey(Pool.subnet), nullable=False)

    def __repr__(self):
        return '%s(%s) - %s from pool %s' % (self.__class__.__name__, self.id, self.hostname, self.pool_subnet)

    @declared_attr
    def pool(cls):
        return db.relationship(Pool, lazy='joined', innerjoin=True,
                  primaryjoin=db.and_(cls.pool_subnet==Pool.subnet),
                  backref=db.backref('nodes', lazy='select', order_by=cls.created.desc()))

    def cleanup_offers(self, mac):
        Lease.query.with_parent(self).delete()
        db.session.commit()

    def offer(self, test_func):
        offer_timeout = datetime.now() - timedelta(seconds=app.config.get('DHCP_OFFER_TIMEOUT', 15))

        # cleanup expired leasing
        Lease.query \
             .filter(Lease.leasing_until==None) \
             .filter(Lease.created < offer_timeout ) \
             .delete()


        existen_leasing = Lease.query.with_parent(self) \
                                     .filter(Lease.leasing_until!=None) \
                                     .first()

        ip = existen_leasing.yiaddr if existen_leasing else self.static_ip

        if not ip or test_func(ip):
            ip = self.pool.subnet.ip + 1
            leasing_ip_list = [ lease.yiaddr for lease in self.pool.leases ]
            while ip <= self.pool.subnet.ip + self.pool.subnet.size:
                if not ip in leasing_ip_list and not test_func(ip):
                    break
                ip += 1

        if existen_leasing:
            db.session.delete(existen_leasing)
            db.session.flush()

        lease = Lease(ip)
        self.leases.append(lease)
        db.session.commit()

        return ip

    def lease(self, ip, existen=None):
        query = Lease.query.with_parent(self).filter(Lease.yiaddr==ip)
        query = query.filter(Lease.leasing_until!=None) if existen else query
        return query.first()

    def decline(self, ip):
        decline = Decline(ip, self.mac)
        db.session.add(decline)
        db.session.commit()

    def commit_lease(self, lease):
        Lease.query.with_parent(self).filter(Lease.yiaddr!=lease.yiaddr).delete()  # remove all other offers
        lease.leasing_until = datetime.now() + timedelta(seconds=self.pool.lease_time)
        db.session.commit()

    def release(self):
        Lease.query.with_parent(self).delete()


class Lease(db.Model):
    __tablename__ = 'leasing'
    id = db.Column(db.String, db.ForeignKey(Node.id), primary_key=True)
    yiaddr = db.Column(Ip, primary_key=True)
    created = db.Column(db.DateTime, default=lambda: datetime.now(), nullable=False)
    leasing_until = db.Column(db.DateTime, nullable=True) # null mean offered

    def __init__(self, yiaddr):
        self.yiaddr = yiaddr

    @declared_attr
    def node(cls):
        return db.relationship(Node, lazy='select', innerjoin=True,
               backref=db.backref('leases', lazy='joined', order_by=cls.created.desc()))

    pool = db.relationship(Pool,
                secondary=Node.__table__, lazy='select', backref='leases', viewonly=True)

    def __repr__(self):
        return "%s - %s(from %s until %s)" % (self.__class__.__name__, self.yiaddr, self.created, self.leasing_until)


class Decline(db.Model):
    __tablename__ = 'decline'
    created = db.Column(db.DateTime, default=lambda: datetime.now(), nullable=False)
    ip = db.Column(Ip, primary_key=True)
    reported_by = db.Column(db.String, db.ForeignKey(Node.id), primary_key=True)

    def __init__(self, ip, reported_by):
        self.ip = ip
        self.reported_by = reported_by
