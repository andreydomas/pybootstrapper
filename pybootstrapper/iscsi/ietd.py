import subprocess
from pybootstrapper.ext import iscsi_images_store
import signals

class IETAdmError(Exception):
    def __init__(self, app, parent):
        self.parent = parent
        app.logger.error('ietadm: %s' % parent)

    def __str__(self):
        return str(self.parent)


class IETAdm(object):

    def __init__(self, app):
        self.app = app
        self.ietadm = app.config.get('IETADM', '/usr/sbin/ietadm')
        signals.create.connect(self.new_lun)

    def new_lun(self, image):
        try:
            subprocess.check_call([
                self.ietadm,
                '--op', 'new',
                '--tid=%d' % image.farm_id,
                '--lun=%d' % image.id,
                '--params',
                'Path=%s,IOMode=ro' % iscsi_images_store.image_path(image.farm_id, image.filename)
            ])
        except subprocess.CalledProcessError, e:
            raise IETAdmError(self.app, e)
