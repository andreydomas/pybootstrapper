from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr

from app.ext import db
from ..models import Fixtured
from ..kernels.models import Kernel

class Farm(db.Model, Fixtured):
    __tablename__ = 'farms'
    id = db.Column(db.Integer(), primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    name = db.Column(db.String(), nullable=False, unique=True)

    def __str__(self):
        return self.name


class BootImage(db.Model, Fixtured):
    __tablename__ = 'boot_images'
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    version = db.Column(db.String(), nullable=False, primary_key=True)
    farm_id = db.Column(db.Integer(), db.ForeignKey(Farm.id), nullable=False, primary_key=True)
    kernel_name = db.Column(db.String(), db.ForeignKey(Kernel.name), nullable=False)

    kernel = db.relationship(Kernel, backref='boot_images', lazy='joined')

    @declared_attr
    def farm(cls):
        return db.relationship(Farm, backref=db.backref('boot_images', innerjoin=True, order_by=cls.version.desc()), innerjoin=True, single_parent=True)

    def __init__(self, farm, version, kernel):
        self.farm = farm
        self.version = version
        self.kernel = kernel

    @property
    def filename(self):
        return self.version

    @property
    def kernel_opts(self):
        pass
