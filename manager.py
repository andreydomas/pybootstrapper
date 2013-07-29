import logging
from flask.ext.script import Manager

from pybootstrapper import create_app
from pybootstrapper.ext import db
from flask.ext.script import Server


def create_app_factory():
    return create_app('../settings.ini')


#class TornadoServer(Server):
#    def handle(self, app, host, port, use_debugger, use_reloader,
#               threaded, processes, passthrough_errors):
#
#        from pybootstrapper.http.server import init
#        #app.run()
#        init(create_app_factory(), port)


manager = Manager(create_app_factory)
#manager.add_command("runserver", TornadoServer())


@manager.command
def sync_db():
    db.create_all(app=create_app_factory())


@manager.command
def drop_db():
    db.drop_all()


@manager.command
def fixtures():
    logger = logging.getLogger('fixtures')
    from os import path
    from yaml import load_all
    from pybootstrapper.nodes.models import Node, Pool, Farm, BootImage
    from pybootstrapper.kernels.models import Kernel

    fixtures_dir = path.dirname(path.realpath(__file__)) + '/fixtures'
    fixtures_classes_factories = {
            'Farm': Farm,
            'Pool': Pool,
            'Kernel': Kernel,
            'BootImage': BootImage,
            'Node': Node,
    }

    sequence = ['Farm', 'Pool', 'Kernel', 'BootImage', 'Node']

    for fx in sequence:
        f = fixtures_dir + '/' + fx
        if path.isfile(f):
            logger.info(f)
            dataMap = load_all(file(f, 'r'))

            chunk = 1

            for entity in dataMap:
                model_cls = fixtures_classes_factories[fx]
                model_obj = model_cls().from_yaml(entity)
                db.session.add(model_obj)
                db.session.flush()

                if chunk / 50:
                    db.session.commit()
            db.session.commit()


@manager.command
def dhcp():
    from pybootstrapper.dhcp.server import init
    init(create_app_factory())


@manager.command
def tftp():
    from pybootstrapper.tftp.server import init
    init(create_app_factory())


if __name__ == "__main__":
        manager.run()
