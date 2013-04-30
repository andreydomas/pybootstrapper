from flask.ext.sqlalchemy import SQLAlchemy
from flaskext.uploads import UploadSet, ALL

__all__ = ['db']

db = SQLAlchemy()
images_store = UploadSet('image', ALL,
                default_dest=lambda app: app.config.get('IMAGES_STORE', '/dev/null')
            )
images_store.resolve_conflict = lambda target_folder, basename: basename
