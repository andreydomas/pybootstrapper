import re
from datetime import datetime, timedelta
from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import get_history
from flask import current_app, url_for
from netaddr import *

from pybootstrapper.ext import db
from ..pools.models import Pool, PoolOption
from ..farms.models import Farm, BootImage
from ..models import Fixtured
from ..sqla_types import *


class Node(Fixtured, db.Model):
    __tablename__ = 'nodes'
    __table_args__ = {'mysql_engine':'InnoDB'}

    id = db.Column(Mac, primary_key=True, autoincrement=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    hostname = db.Column(db.String(255), nullable=False)
    static_ip = db.Column(Ip, nullable=True)
    pool_subnet = db.Column(Subnet(18), db.ForeignKey(Pool.subnet, onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey(BootImage.id))

    def __repr__(self):
        return '%s(%s) - %s from pool %s' % (self.__class__.__name__, self.id, self.hostname, self.pool)

    @declared_attr
    def pool(cls):
        return db.relationship(Pool, lazy='joined', innerjoin=True,
                  primaryjoin=db.and_(cls.pool_subnet==Pool.subnet),
                  backref=db.backref('nodes', lazy='select', order_by=cls.created.desc()))

    farm = db.relationship(Farm, backref='nodes', secondary=Pool.__table__, uselist=False, lazy='joined')

    boot_image = db.relationship(BootImage, backref='nodes', lazy='joined')

    def cleanup_offers(self):
        Lease.query.with_parent(self).delete()
        db.session.commit()

    def offer(self, test_func):
        offer_timeout = datetime.now() - timedelta(seconds=15)

        # cleanup expired uncommited leasings
        Lease.query \
             .filter(Lease.leasing_until==None) \
             .filter(Lease.created < offer_timeout) \
             .delete()


        # get commited leasing
        existen_leasing = Lease.query.with_parent(self) \
                                     .filter(Lease.leasing_until!=None, Lease.force_expire==False) \
                                     .first()

        ip = self.static_ip or (existen_leasing.yiaddr if existen_leasing else None)

        if not ip or test_func(ip):
            ip = self.pool.subnet.ip + 1
            leasing_ip_list = [ lease.yiaddr for lease in self.pool.leases ]
            while ip <= self.pool.subnet.ip + self.pool.subnet.size:
                if not ip in leasing_ip_list and not test_func(ip):
                    break
                ip += 1

        Lease.query.with_parent(self).filter(db.or_(Lease.force_expire==True, Lease.yiaddr==ip)).delete(synchronize_session='fetch')
        db.session.flush()

        lease = Lease(ip)
        self.leases.append(lease)
        db.session.add(lease)
        db.session.commit()

        return ip

    def lease(self, ip, existen=None):
        query = Lease.query.with_parent(self).filter(Lease.yiaddr==ip, Lease.force_expire==False)
        query = query.filter(Lease.leasing_until!=None) if existen else query.filter(Lease.leasing_until==None)
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
        self.cleanup_offers()


    def _options(self, add):
        lease_time = None

        yield PoolOption('subnet_mask', str(self.pool.subnet.netmask))

        for opt in self.pool.options:
            if opt.option == 'ip_address_lease_time':
                lease_time = opt
            yield opt

        for opt in add:
            if opt.option == 'ip_address_lease_time':
                lease_time = opt
            yield opt

        yield PoolOption('host_name', self.hostname)

        if not lease_time:
            yield PoolOption('ip_address_lease_time', current_app.config.get('DHCP_LEASE_TIME', 3600))

    @property
    def pxe_options(self):
        return self._options([
                    PoolOption('bootfile_name', 'gpxelinux.0'),
                    PoolOption('tftp_server_name', current_app.config.get('TFTP_LISTEN')),
                ])


    @property
    def gpxe_options(self):
        return self._options([
                    PoolOption('bootfile_name',
                    #    # url_for cannot be used because it depends on SERVER_NAME
                    #    # but werkzeug tests port number in Host header and gpxelinux strips the number from the header
                        '%s/nodes/%s/gpxelinux.conf' % (current_app.config['GPXELINUX_HTTP_PREFIX'], self.id)
                    )
                ])

@event.listens_for(Node, 'before_update')
def leasing_force_expiration(mapper, connection, target):

    expired = False

    added, unchanged, deleted = get_history(target, 'static_ip')
    expired = expired or added or deleted

    added, unchanged, deleted = get_history(target, 'pool_subnet')
    expired = expired or added or deleted

    if expired:
       Lease.query.with_parent(target).update({'force_expire': True})


class Lease(db.Model):
    __tablename__ = 'leasing'
    __table_args__ = {'mysql_engine':'InnoDB'}

    id = db.Column(Mac, db.ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True, autoincrement=False)
    yiaddr = db.Column(Ip, primary_key=True, autoincrement=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    leasing_until = db.Column(db.DateTime, nullable=True) # null mean offered
    force_expire = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, yiaddr=None):
        self.yiaddr = yiaddr

    @declared_attr
    def node(cls):
        return db.relationship(Node,
                    lazy='select', innerjoin=True,
                    backref=db.backref('leases', lazy='joined', order_by=cls.created.desc()))

    pool = db.relationship(Pool,
                secondary=Node.__table__, lazy='select', backref='leases', viewonly=True)

    def __repr__(self):
        return "%s - %s(from %s until %s)" % (self.__class__.__name__, self.yiaddr, self.created, self.leasing_until)


class Decline(db.Model):
    __tablename__ = 'decline'
    __table_args__ = {'mysql_engine':'InnoDB'}

    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    ip = db.Column(Ip, primary_key=True, autoincrement=False)
    reported_by = db.Column(Mac, db.ForeignKey(Node.id, ondelete='CASCADE'), primary_key=True, autoincrement=False)

    def __init__(self, ip, reported_by):
        self.ip = ip
        self.reported_by = reported_by
