import logging
from flask.ext.script import Manager

from app import app, db

if not app.debug:
    log_level = logging.WARN
else:
    log_level = logging.DEBUG
logging.basicConfig(level=log_level, format=app.config.get('LOG_FORMAT', '%(levelname)-8s [%(asctime)s]  %(message)s'))

manager = Manager(app)

@manager.command
def sync_db():
    db.create_all(app=app)

@manager.command
def drop_db():
    db.drop_all()

@manager.command
def fixtures():
    logger = logging.getLogger('fixtures')
    from os import path
    from yaml import load_all
    from app.nodes.models import Node, Pool

    fixtures_dir = path.dirname(path.realpath(__file__)) + '/fixtures'
    fixtures_classes_factories = {
            'Node': Node,
            'Pool': Pool,
    }

    sequence = ['Pool', 'Node']

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
    init(app.config)

if __name__ == "__main__":
        manager.run()
