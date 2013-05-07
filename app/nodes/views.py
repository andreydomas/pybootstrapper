from flask import Blueprint, render_template, current_app, request, redirect


from app.ext import db

import models
import forms

mod = Blueprint('nodes', __name__, url_prefix='/nodes')

@mod.route('/', methods=['GET'])
def list():
    nodes = models.Node.query.all()
    return render_template("nodes/list.html", nodes=nodes)

@mod.route('/<string:id>', methods=['GET', 'POST'])
def node(id):

    node = None
    code = 200
    if id:
        node = models.Node.query.get_or_404(id)

    if request.method == 'POST':

        form = forms.NodeForm()
        if form.validate_on_submit():
            if not node:
                node = models.Node()
                db.session.add(node)
                code = 201

            form.populate_obj(node)
            db.session.commit()

        else:
            code = 400
            current_app.logger.error(form.errors)

    else:
        form = forms.NodeForm(obj=node)

    return render_template("nodes/node.html", node=node, form=form), code
