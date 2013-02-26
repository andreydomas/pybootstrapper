from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr

from app import db
from ..nodes.models import Node

class Lease(db.Model):
    created = created = db.Column(db.DateTime, default=datetime.now(), primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey(Node.mac), primary_key=True)
    leasing_due = db.Column(db.DateTime, nullable=True)

    @declared_attr
    def node(cls):
        return db.relationship(Node, lazy='joined', innerjoin=True,
               backref=db.backref('leases', lazy='select', order_by=cls.created.desc()))
