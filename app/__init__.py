from flask import Flask, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('../settings.ini')

@app.route('/')
def redirect_to_default():
    return redirect(url_for('nodes.list'))

db = SQLAlchemy(app)
db.init_app(app)

from app.nodes.views import mod as nodesModule
app.register_blueprint(nodesModule)

from app.pools.views import mod as poolsModule
app.register_blueprint(poolsModule)
