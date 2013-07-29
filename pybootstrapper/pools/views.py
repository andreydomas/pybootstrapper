from flask import Blueprint, render_template, request, current_app
from netaddr import IPNetwork, AddrFormatError

from pybootstrapper.ext import db
from ..nodes.models import Lease

import models
import forms

mod = Blueprint('pools', __name__, url_prefix='/pools')

@mod.route('/', methods=['GET'])
def list():
    pools = models.Pool.query.options(
                db.undefer('nodes_count'),
                db.joinedload('farm')
            ).paginate(int(request.args.get('p', 1)))
    return render_template("pools/list.html", pools=pools)


def get_pool_by_id(id):
    try:
        subnet = IPNetwork(id.replace("_", "/"))
        print subnet
    except AddrFormatError:
        return models.Pool.query.filter(models.Pool.name==id).first_or_404()
    else:
        return models.Pool.query.get_or_404(subnet)


@mod.route('/<id>/nodes', methods=['GET'])
def nodes(id):
    pool = get_pool_by_id(id)
    return render_template("nodes/list.html",
                nodes=pool.nodes.paginate(int(request.args.get('p', 1))),
                caption='Pool %s nodes' % pool.subnet,
                pool=pool)


@mod.route('/<id>/leases', methods=['GET'])
@mod.route('/leases', methods=['GET'], defaults={'id': None})
def leases(id):
    leases = None
    caption = None
    pool = None

    if id:
        pool = get_pool_by_id(id)
        leases = pool.leases
        caption = 'Pool %s leases' % pool.subnet

    else:
        leases = Lease.query

    return render_template("leases/list.html",
            leases=leases.paginate(int(request.args.get('p', 1))),
            caption=caption,
            pool=pool)


@mod.route('/__new__', methods=['POST', 'GET'], defaults={'id': None})
@mod.route('/<id>', methods=['GET', 'POST'])
def pool(id):

    pool = None
    code = 200

    if id:
        pool = get_pool_by_id(id)

    form = forms.PoolForm(obj=pool)

    if form.validate_on_submit():

        if not pool:
            pool = models.Pool()
            code = 201

        else:
            code = 200

        form.populate_obj(pool)
        db.session.add(pool)
        db.session.commit()

    else:
        if form.errors:
            code = 400
            current_app.logger.error(form.errors)

    return render_template("pools/pool.html", pool=pool, form=form), code


@mod.route('/<string:id>/images', methods=['GET'])
def images(id):
    pool = get_pool_by_id(id)
    if request.is_xhr:
        return ''.join([ '<option value=%s>%s</option>' % (image.version, image) for image in pool.farm.boot_images ])
