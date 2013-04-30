from flask import Blueprint, render_template, request, current_app

from app.ext import db
from ..nodes.models import Lease

import models
import forms

mod = Blueprint('pools', __name__, url_prefix='/pools')

@mod.route('/', methods=['GET'])
def list():
    pools = models.Pool.query.all()
    return render_template("pools/list.html", pools=pools)


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


@mod.route('/new', methods=['POST', 'GET'], defaults={'id': None})
@mod.route('/<id>', methods=['GET', 'POST'])
def pool(id):

    pool = None
    code = 200

    if id:
        pool = models.Pool.query.get_or_404(id.replace("_", "/"))

    if request.method == 'POST':

        form = forms.PoolForm()
        if form.validate_on_submit():

            if not pool:
                pool = models.Pool()
                db.session.add(pool)
                code = 201

            form.populate_obj(pool)
            db.session.commit()

        else:
            code = 400
            current_app.logger.error(form.errors)

    else: # if not POST
        form = forms.PoolForm(obj=pool)

    return render_template("pools/pool.html", pool=pool, form=form), code
