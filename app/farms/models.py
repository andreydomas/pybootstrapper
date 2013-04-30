from datetime import datetime

from app.ext import db
from ..models import Fixtured

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
    farm = db.relationship(Farm, backref=db.backref('boot_images', innerjoin=True), innerjoin=True, single_parent=True)

    def __init__(self, farm, version):
        self.farm = farm
        self.version = version

    @property
    def filename(self):
        return self.version

    @property
    def tftp_path(self):
        return '/'.join(('', str(self.farm_id), self.filename))
