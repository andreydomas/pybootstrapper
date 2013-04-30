import logging
from flask.ext.script import Manager

from app import create_app
from app.ext import db

manager = Manager(create_app)

@manager.command
def sync_db():
    db.create_all(app=create_app())

@manager.command
def drop_db():
    db.drop_all()

@manager.command
def fixtures():
    logger = logging.getLogger('fixtures')
    from os import path
    from yaml import load_all
    from app.nodes.models import Node, Pool, Farm

    fixtures_dir = path.dirname(path.realpath(__file__)) + '/fixtures'
    fixtures_classes_factories = {
            'Farm': Farm,
            'Node': Node,
            'Pool': Pool,
    }

    sequence = ['Farm', 'Pool', 'Node']

    for fx in sequence:
        f = fixtures_dir + '/' + fx
        instances = list()
        if path.isfile(f):
            logger.info(f)
            dataMap = load_all(file(f, 'r'))
            for entity in dataMap:
                model_cls = fixtures_classes_factories[fx]
                model_obj = model_cls().from_yaml(entity)
                instances.append(model_obj)
            db.session.add_all(instances)
            db.session.commit()

@manager.command
def dhcp():
    from app.dhcp.server import init
    init(create_app)

if __name__ == "__main__":
        manager.run()
