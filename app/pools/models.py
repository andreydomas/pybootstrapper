from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property

from app import db, app
from ..models import Fixtured
from ..sqla_types import *

class Pool(Fixtured, db.Model):
    __tablename__ = 'pools'

    def __init__(self, subnet=None):
        self.subnet = subnet

    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    subnet = db.Column(Subnet(18), primary_key=True)
    router = db.Column(Ip, nullable=True)
    domain = db.Column(db.String(253), nullable=False)
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
