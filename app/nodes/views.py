from flask import Blueprint, render_template

import models
import forms

mod = Blueprint('nodes', __name__, url_prefix='/nodes')

@mod.route('/', methods=['GET'])
def list():
    nodes = models.Node.query.all()
    return render_template("nodes/list.html", nodes=nodes)

@mod.route('/<id>', methods=['GET', 'POST'])
def node(id):
    node = models.Node.query.get_or_404(id)
    return render_template("nodes/node.html", node=node, form=form)
