from flask import Flask, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy, models_committed
from flaskext.uploads import configure_uploads

from pybootstrapper.ext import db, pxe_images_store, kernels_store, iscsi_images_store

__all__ = ["create_app"]


def create_app(settings_ini):
    app = Flask(__name__)
    app.config.from_pyfile(settings_ini)
    init_db(app)
    init_ext(app)
    init_blueprints(app)
    init_iscsi(app)

    if app.config.get('DEBUG'):
        init_debug(app)

    return app


def init_db(app):
    from sqlalchemy.engine import Engine
    from sqlalchemy import event

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if dbapi_connection.__class__.__module__ == 'sqlite3':
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    #@models_committed.connect_via(app)
    #def model_committed(sender, changes):
    #    for change in changes:
    #        model, operation = change
    #        if hasattr(model, '__model_committed__') and hasattr(model.__model_committed__, '__call__'):
    #            model.__model_committed__(operation)

    db.init_app(app)

def init_iscsi(app):
    from iscsi.ietd import IETAdm
    app.ietd = IETAdm(app)

def init_debug(app):
    from flask_debugtoolbar import DebugToolbarExtension
    DebugToolbarExtension(app)

def init_ext(app):
    configure_uploads(app, pxe_images_store)
    configure_uploads(app, kernels_store)
    configure_uploads(app, iscsi_images_store)


def init_blueprints(app):

    from  pybootstrapper.events.views import mod as eventsModule
    app.register_blueprint(eventsModule)

    from pybootstrapper.nodes.views import mod as nodesModule
    app.register_blueprint(nodesModule)

    from pybootstrapper.pools.views import mod as poolsModule
    app.register_blueprint(poolsModule)

    from pybootstrapper.farms.views import mod as farmsModule
    app.register_blueprint(farmsModule)

    from pybootstrapper.kernels.views import mod as kernelsModule
    app.register_blueprint(kernelsModule)

    @app.route('/')
    def redirect_to_default():
        return redirect(url_for('events.list'))
