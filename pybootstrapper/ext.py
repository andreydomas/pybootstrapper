from flask.ext.sqlalchemy import SQLAlchemy
from flaskext.uploads import UploadSet, ALL

__all__ = ['db']

db = SQLAlchemy()


iscsi_images_store = UploadSet('iscsiImage', extensions=ALL,
                default_dest=lambda app: app.config.get('ISCSI_IMAGES_STORE', '/dev/null')
            )
iscsi_images_store.resolve_conflict = lambda target_folder, basename: basename

pxe_images_store = UploadSet('pxeImage', extensions=ALL,
                default_dest=lambda app: app.config.get('PXE_IMAGES_STORE', '/dev/null')
            )
pxe_images_store.resolve_conflict = lambda target_folder, basename: basename

kernels_store = UploadSet('kernel', extensions=ALL,
                default_dest=lambda app: app.config.get('KERNELS_STORE', '/dev/null')
            )
kernels_store.resolve_conflict = lambda target_folder, basename: basename
