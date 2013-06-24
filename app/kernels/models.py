from datetime import datetime

from app.ext import db
from ..models import Fixtured

class Kernel(db.Model, Fixtured):
    __tablename__ = 'kernels'
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    name = db.Column(db.String(), nullable=False, primary_key=True)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name
