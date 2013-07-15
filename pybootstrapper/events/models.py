from datetime import datetime

from flask import url_for, Markup
from sqlalchemy.ext.hybrid import hybrid_property

from pybootstrapper.ext import db
import constants

class PyBootstrapperEvent(db.Model):
    __tablename__ = 'events'
    __table_args__ = {'mysql_engine':'InnoDB'}

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.now)
    type = db.Column(db.Enum(*constants.types._asdict().values()))
    _message = db.Column('message', db.Text(65535))
    payload = db.Column(db.Text(65535), nullable=True) # it's for URI for action

    __mapper_args__ = {
       'polymorphic_identity': constants.types.base,
       'polymorphic_on': type,
       'with_polymorphic': '*'
    }

    level = 'info'

    def __init__(self, message, payload=None):
        self._message = message
        self.payload = payload


    @hybrid_property
    def message(self):
        return self._message

    def get_message(self):
        return self._message

    def set_message(self, val):
        self._message = val

    @classmethod
    def register(cls, message, payload):
        event = cls(message, payload)
        db.session.add(event)


class PyBootstrapperEventDhcpUnknownHost(PyBootstrapperEvent):
    __mapper_args__ = {
       'polymorphic_identity': constants.types.dhcp_unknown_host,
    }

    level = 'warning'

    @hybrid_property
    def message(self):
        return Markup(self._message.replace(self.payload,
                    '<a href="%s">%s</a>' % (url_for('nodes.node', id=self.payload), self.payload)
                ))

    @classmethod
    def register(cls, payload):
        super(PyBootstrapperEventDhcpUnknownHost, cls).register('Got DHCP DISCOVER from unknown host: %s' % payload, payload)
        db.session.commit()


class PyBootstrapperEventDhcpLeasing(PyBootstrapperEvent):
    __mapper_args__ = {
       'polymorphic_identity': constants.types.dhcp_leasing,
    }

    level = 'success'

    @hybrid_property
    def message(self):
        return Markup(self._message.replace(self.payload,
                    '<a href="%s">%s</a>' % (url_for('nodes.node', id=self.payload), self.payload)
                ))

    @classmethod
    def register(cls, payload, ip):
        super(PyBootstrapperEventDhcpLeasing, cls).register('Host %s got ip %s' % (payload, ip), payload)
        db.session.commit()


class PyBootstrapperEventFilesNewImage(PyBootstrapperEvent):
    __mapper_args__ = {
       'polymorphic_identity': constants.types.files_new_image,
    }

    @hybrid_property
    def message(self):
        return Markup(self._message.replace(self.payload,
                    '<a href="%s">%s</a>' % (url_for('farms.farm', name=self.payload), self.payload)
                ))

    @classmethod
    def register(cls, version, farm):
        super(PyBootstrapperEventFilesNewImage, cls).register('The image version %s for farm %s has been uploaded' % (version, farm.name), farm.name)


class PyBootstrapperEventFilesNewKernel(PyBootstrapperEvent):
    __mapper_args__ = {
       'polymorphic_identity': constants.types.files_new_kernel,
    }

    @hybrid_property
    def message(self):
        return Markup(self._message.replace(self.payload,
                    '<b>%s</b>' % self.payload)
                )

    @classmethod
    def register(cls, payload):
        super(PyBootstrapperEventFilesNewKernel, cls).register('The kernel %s has been uploaded' % payload, payload)
