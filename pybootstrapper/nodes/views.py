from flask import Blueprint, render_template, current_app, request, send_file

from pybootstrapper.ext import db, pxe_images_store, kernels_store
from ..farms.models import BootImage
import models
import forms


mod = Blueprint('nodes', __name__, url_prefix='/nodes')

@mod.route('/', methods=['GET'])
def list():
    nodes = models.Node.query.paginate(int(request.args.get('p', 1)))
    return render_template("nodes/list.html", nodes=nodes)


@mod.route('/<string:id>/gpxelinux.conf', methods=['GET'])
def gpxelinux_conf(id):
    node = models.Node.query.get_or_404(id)
    return render_template("nodes/gpxelinux.conf", lines=node.boot_image.gpxelinux(node))


@mod.route('/<string:id>/kernel', methods=['GET'])
def kernel(id):
    node = models.Node.query.get_or_404(id)
    return send_file(
                kernels_store.path(node.boot_image.kernel.name),
                mimetype='application/octet-stream',
                add_etags=False
            )


@mod.route('/<string:id>/initrd', methods=['GET'])
def initrd(id):
    node = models.Node.query.get_or_404(id)
    return send_file(
                pxe_images_store.image_path(node.boot_image.farm_id, node.boot_image.filename),
                mimetype='application/octet-stream',
                add_etags=False
            )


@mod.route('/<string:id>', methods=['GET', 'POST'])
def node(id):

    code = 200
    node = models.Node.query.get(id)
    form = forms.NodeForm(obj=node)

    if node:
        form.boot_image.query_factory = lambda: node.farm.boot_images
    else:
        form.boot_image.query_factory = BootImage.query.all
        form.id.data = id

    if form.validate_on_submit():
        if not node:
            node = models.Node()
            db.session.add(node)
            code = 201
        else:
            code = 200

        form.populate_obj(node)
        db.session.commit()

    else:
        if form.errors:
            current_app.logger.error(form.errors)
            code = 400

    return render_template("nodes/node.html", node=node, form=form), code
