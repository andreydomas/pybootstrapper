from flask import Blueprint, render_template, current_app, request, send_file

from app.ext import db, images_store, kernels_store
import models
import forms


mod = Blueprint('nodes', __name__, url_prefix='/nodes')

@mod.route('/', methods=['GET'])
def list():
    nodes = models.Node.query.all()
    return render_template("nodes/list.html", nodes=nodes)


@mod.route('/<string:id>/gpxelinux.conf', methods=['GET'])
def gpxelinux_conf(id):
    node = models.Node.query.get_or_404(id)
    return render_template("nodes/gpxelinux.conf", node=node, GPXELINUX_HTTP_PREFIX=current_app.config['GPXELINUX_HTTP_PREFIX'])


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
                images_store.path('%s/%s' % (node.boot_image.farm_id, node.boot_image.filename)),
                mimetype='application/octet-stream',
                add_etags=False
            )


@mod.route('/<string:id>', methods=['GET', 'POST'])
def node(id):

    node = None
    code = 200
    form = forms.NodeForm()

    if id:
        node = models.Node.query.get_or_404(id)
        form.boot_image.query_factory = lambda: node.farm.boot_images

    if request.method == 'POST':
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
        form.process(obj=node)

    return render_template("nodes/node.html", node=node, form=form), code
