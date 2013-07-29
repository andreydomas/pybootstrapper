import subprocess
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr

from flask import current_app, url_for, abort

from pybootstrapper.ext import db, iscsi_images_store
from ..models import Fixtured
from ..kernels.models import Kernel
import constants


class Farm(db.Model, Fixtured):
    __tablename__ = 'farms'
    __table_args__ = {'mysql_engine':'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    name = db.Column(db.String(255), nullable=False, unique=True)

    def __str__(self):
        return self.name


class BootImage(db.Model, Fixtured):
    __tablename__ = 'images'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    image_type = db.Column(db.Enum(*constants.images_types._asdict().values()), nullable=False)
    version = db.Column(db.String(255), nullable=False)

    __mapper_args__ = {
       'polymorphic_on': image_type,
       'with_polymorphic': '*'
    }

    farm_id = db.Column(db.Integer, db.ForeignKey(Farm.id, ondelete='CASCADE'), nullable=False)

    @declared_attr
    def kernel_name(cls):
        return db.Column(db.String(255), db.ForeignKey(Kernel.name, ondelete='CASCADE'))

    @declared_attr
    def kernel(cls):
        return db.relationship(Kernel, backref=db.backref('boot_images', lazy='select'), lazy='joined')

    @declared_attr
    def farm(cls):
        return db.relationship(Farm,
                        backref=db.backref('boot_images', lazy='dynamic', innerjoin=True, order_by=cls.version.desc()),
                        lazy='joined',
                        innerjoin=True, single_parent=True)

    @classmethod
    def __declare_last__(cls):
        Kernel.boot_images_count = db.column_property(db.select([db.func.count()]) \
                                                        .where(
                                                            cls.kernel_name==Kernel.name
                                                        ) \
                                                        .label('boot_images_count'),
                                                        deferred=True
                                                    )

        Farm.boot_images_count = db.column_property(db.select([db.func.count()]) \
                                                        .where(
                                                            cls.farm_id==Farm.id
                                                        ) \
                                                        .label('boot_images_count'),
                                                        deferred=True
                                                    )



    __table_args__ = (
            db.UniqueConstraint(image_type, version, farm_id),
            db.CheckConstraint(
                db.or_(
                    db.and_(
                        image_type==constants.images_types.PXE,
                        'kernel_name IS NOT NULL'
                    ),
                    db.and_(
                        image_type==constants.images_types.ISCSI,
                        'kernel_name IS NULL'
                    )
                )
            ),

            {'mysql_engine':'InnoDB'}
    )

    def __init__(self, farm=None, version=None):
        self.farm = farm
        self.version = version

    def __repr__(self):
        return '%s - %s (%s)' % (self.version, self.farm, self.image_type)

    @property
    def filename(self):
        return self.version

    @property
    def kernel_opts(self):
        pass

    def gpxelinux(self):
        raise NotImplementedError


class PxeBootImage(BootImage):
    __mapper_args__ = {
       'polymorphic_identity': constants.images_types.PXE
    }

    def gpxelinux(self, node):
        return'kernel %(prefix)s%(kernel)s\ninitrd %(prefix)s%(initrd)s' % {
                'prefix': current_app.config['GPXELINUX_HTTP_PREFIX'],
                'kernel': url_for('nodes.kernel', id=node.id),
                'initrd': url_for('nodes.initrd', id=node.id),
        }


class IscsiBootImage(BootImage):
    __mapper_args__ = {
       'polymorphic_identity': constants.images_types.ISCSI
    }

    def gpxelinux(self, node):
        return 'sanboot iscsi:%(server)s:::%(lun)x:%(target)s' % {
                    'server': current_app.config['ISCSI_SERVER'],
                    'lun': self.id,
                    'target': current_app.config['ISCSI_TARGET']
                }
