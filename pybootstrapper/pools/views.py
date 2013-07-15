from flask import Blueprint, render_template, request, current_app
from netaddr import IPNetwork, AddrFormatError

from pybootstrapper.ext import db
from ..nodes.models import Lease

import models
import forms

mod = Blueprint('pools', __name__, url_prefix='/pools')

@mod.route('/', methods=['GET'])
def list():
    pools = models.Pool.query.all()
    return render_template("pools/list.html", pools=pools)


def get_pool_by_id(id):
    try:
        subnet = IPNetwork(id.replace("_", "/"))
    except AddrFormatError:
        pool = models.Pool.query.filter(models.Pool.name==id).first_or_404()
    else:
        pool = models.Pool.query.get_or_404(subnet)

    return pool


@mod.route('/<id>/nodes', methods=['GET'])
def nodes(id):
    pool = models.Pool.query.get_or_404(id.replace("_", "/"))
    return render_template("nodes/list.html", nodes=pool.nodes, caption='Pool %s nodes' % pool.subnet)


@mod.route('/<id>/leases', methods=['GET'])
@mod.route('/leases', methods=['GET'], defaults={'id': None})
def leases(id):
    leases = None
    caption = None
    if id:
        pool = models.Pool.query.get_or_404(id.replace("_", "/"))
        leases = pool.leases
        caption = 'Pool %s leases' % pool.subnet

    else:
        leases = Lease.query.all()

    return render_template("leases/list.html", leases=leases, caption=caption)


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
