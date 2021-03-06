import re
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr

from pybootstrapper.ext import db
from ..models import Fixtured
from ..farms.models import Farm
from ..sqla_types import *
from ..dhcp.pydhcplib.dhcp_constants import DhcpOptions, DhcpOptionsTypes, DhcpOptionsList
from ..dhcp.pydhcplib.type_strlist import strlist
from ..dhcp.pydhcplib.type_ipv4 import ipv4


class Pool(Fixtured, db.Model, object):
    __tablename__ = 'pools'
    __table_args__ = {'mysql_engine':'InnoDB'}

    def __init__(self, subnet=None):
        self.subnet = subnet

    def __str__(self):
        return str(self.name or self.subnet)

    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    name = db.Column(db.String(253), nullable=True, unique=True)
    subnet = db.Column(Subnet(18), primary_key=True, autoincrement=False)
    lease_time = db.Column(db.Integer, nullable=False, default=86400)
    farm_id = db.Column(db.Integer(), db.ForeignKey(Farm.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    farm = db.relationship(Farm, backref=db.backref('pools', lazy='dynamic'), single_parent=True, innerjoin=True)

    @classmethod
    def __declare_last__(cls):
        Farm.pools_count = db.column_property(db.select([db.func.count()]) \
                                                .where(
                                                    cls.farm_id==Farm.id
                                                ) \
                                                .label('pools_count'),
                                                deferred=True
                                            )

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, opts_list):
        # remove missing options
        PoolOption.query.with_parent(self).delete()
        self._options.extend(opts_list)


class PoolOption(Fixtured, db.Model):
    __tablename__ = 'pools_options'
    __table_args__ = {'mysql_engine':'InnoDB'}

    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    pool_subnet = db.Column(Subnet(18), db.ForeignKey(Pool.subnet, onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    _option = db.Column('option', db.String(253), nullable=False, primary_key=True)
    value = db.Column(db.String(253), nullable=False)
    pool = db.relationship(Pool, lazy='select', innerjoin=True, single_parent=True, uselist=False,
                backref='_options'
            )

    def __init__(self, option, value):
        self.option = option
        self.value = value

    def __str__(self):
        return '%s = %s' % (self._option, self.value)

    def set_option(self, value):
        self._option = value

    def get_option(self):
        if self._option in DhcpOptionsList:
            return self._option
        return self._option.split('::')[0]

    @declared_attr
    def option(cls):
        return db.synonym('_option', descriptor=property(cls.get_option, cls.set_option))

    @property
    def option_key(self):
        return self.value

    @property
    def optnum(self):
        return DhcpOptions[self.option]

    @property
    def opttype(self):
        t =  DhcpOptionsTypes[self.optnum]
        if t != 'Unassigned':
            return t
        else:
            t = self._option.split('::')[1]
            DhcpOptionsTypes[self.optnum] = t
            return t

    @property
    def binary(self):
        return  {
            'ipv4': self._ipv4,
            'ipv4+': self._ipv4_plus,
            '32-bits': self._32bit,
            '16-bits': self._16bit,
            'char': self._char,
            'bool': self._bool,
            'string': self._string
        }[self.opttype]()

    def _ipv4(self):
        return map(int, self.value.split("."))

    def _ipv4_plus(self):
        result = []
        iplist = self.value.split(",")
        for ip in iplist:
            result += map(int, ip.split("."))
        return result

    def _32bit(self):
        digit = int(self.value)
        return [digit>>24&0xFF,(digit>>16)&0xFF,(digit>>8)&0xFF,digit&0xFF]

    def _16bit(self):
        digit = int(self.value)
        return [(digit>>8)&0xFF,digit&0xFF]

    def _char(self):
        digit = int(self.value)
        return [digit&0xFF]

    def _bool(self):
        if self.value=="False" or self.value=="false" or self.value==0 :
            return [0]
        else:
            return [1]

    def _string(self):
        return strlist(str(self.value)).list()
