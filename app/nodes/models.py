from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr

from app import db
from ..models import Fixtured

class Pool(Fixtured, db.Model):
    __tablename__ = 'pools'
    created = db.Column(db.DateTime, nullable=False, default=datetime.now())
    subnet = db.Column(db.String(21), primary_key=True)
    router = db.Column(db.String(18), nullable=True)
    domain = db.Column(db.String(255), nullable=False)

    @db.validates('subnet')
    @db.validates('router')
    def validate_subnet(self, key, subnet):
        return subnet

class Node(Fixtured, db.Model):
    __tablename__ = 'nodes'
    mac = db.Column(db.String(18), primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now())
    hostname = db.Column(db.String(255), nullable=False)
    static_ip = db.Column(db.String(18), nullable=True)
    pool_subnet = db.Column(db.String, db.ForeignKey(Pool.subnet), nullable=False)

    @declared_attr
    def pool(cls):
        return db.relationship(Pool, lazy='joined', innerjoin=True,
                  backref=db.backref('nodes', lazy='select', order_by=cls.created.desc()))

    @db.validates('mac')
    def validate_mac(self, key, mac):
        return mac

    @db.validates('static_ip')
    def validate_ip(self, key, ip):
        return ip

    @classmethod
    def by_mac(cls, mac):
        return cls.query.get(mac)
