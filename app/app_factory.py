from flask import Flask, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flaskext.uploads import configure_uploads

from app.ext import db, images_store

__all__ = ["create_app"]

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../settings.ini')
    init_ext(app)
    init_blueprints(app)
    return app


def init_ext(app):
    db.init_app(app)
    configure_uploads(app, images_store)


def init_blueprints(app):
    from app.nodes.views import mod as nodesModule
    app.register_blueprint(nodesModule)

    from app.pools.views import mod as poolsModule
    app.register_blueprint(poolsModule)

    from app.farms.views import mod as farmsModule
    app.register_blueprint(farmsModule)

    @app.route('/')
    def redirect_to_default():
        return redirect(url_for('nodes.list'))
