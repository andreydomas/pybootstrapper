from flask import Blueprint, render_template, request, current_app

from app import db
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
    return render_template("nodes/list.html", nodes=pool.nodes)


@mod.route('/<id>/leases', methods=['GET'])
@mod.route('/leases', methods=['GET'], defaults={'id': None})
def leases(id):
    leases = None
    if id:
        pool = models.Pool.query.get_or_404(id.replace("_", "/"))
        leases = pool.leases

    else:
        leases = Lease.query.all()

    return render_template("leases/list.html", leases=leases)


@mod.route('/', methods=['POST'], defaults={'id': None})
@mod.route('/<id>', methods=['GET', 'POST'])
def pool(id):

    pool = None
    if id:
        pool = models.Pool.query.get_or_404(id.replace("_", "/"))

    if request.method == 'POST':
        form = forms.PoolForm(request.form)

        if form.validate_on_submit():

            if not pool:
                pool = models.Pool()
                db.session.add(pool)

            form.populate_obj(pool)
            db.session.commit()

        else:
            current_app.logger.error(form.errors)

    else: # if not POST
        form = forms.PoolForm(obj=pool)

    return render_template("pools/pool.html", pool=pool, form=form)
