from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('../settings.ini')

db = SQLAlchemy(app)
db.init_app(app)

from app.nodes.views import mod as nodesModule
app.register_blueprint(nodesModule)
