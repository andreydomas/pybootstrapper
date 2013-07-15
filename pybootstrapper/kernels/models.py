from datetime import datetime

from pybootstrapper.ext import db
from ..models import Fixtured

class Kernel(db.Model, Fixtured):
    __tablename__ = 'kernels'
    __table_args__ = {'mysql_engine':'InnoDB'}

    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    name = db.Column(db.String(255), nullable=False, primary_key=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name
