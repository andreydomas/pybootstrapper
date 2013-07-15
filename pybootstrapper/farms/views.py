from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app
from werkzeug import secure_filename

from pybootstrapper.ext import db, pxe_images_store, iscsi_images_store
from pybootstrapper import events
from ..pools.models import Pool
from ..kernels.models import Kernel

import models
import forms

mod = Blueprint('farms', __name__, url_prefix='/farms')


def gexf(farms):
    return render_template("farms/gexf.xml", farms=farms)

@mod.route('/', methods=['GET'])
def list():
    farms = models.Farm.query.all()

    if 'gexf' in request.args:
        return gexf(farms)

    return render_template("farms/list.html", farms=farms)


@mod.route('/<string:name>/pools', methods=['GET'])
def pools(name):
    farm = models.Farm.query.filter(models.Farm.name==name).first_or_404()
    return render_template("pools/list.html", pools=farm.pools, caption='Farm %s pools' % farm.name)


@mod.route('/<string:name>/nodes', methods=['GET'])
def nodes(name):
    farm = models.Farm.query.filter(models.Farm.name==name).first_or_404()
    return render_template("nodes/list.html", nodes=farm.nodes, caption='Farm %s nodes' % farm.name)


@mod.route('/<string:name>/nodes', methods=['POST'])
def new_node(name, pool, mac):
    farm = models.Farm.query.filter(models.Farm.name==name).first_or_404()
    pool = Pool.query.with_parent(farm).filter(Pool.subnet==pool).first_or_404()


@mod.route('/<string:name>/images', methods=['GET'])
@mod.route('/images', methods=['GET'], defaults={'name': None})
def images(name):
    if name:
        farm = models.Farm.query.filter(models.Farm.name==name).first_or_404()
        caption='Farm %s images' % farm.name
        images = farm.boot_images
    else:
        caption = None
        images = models.PxeBootImage.query.all()

    return render_template("farms/images.html", images=images, caption=caption)


@mod.route('/<string:name>/images/pxe/<string:kernel_name>/<string:version>', methods=['PUT'])
@mod.route('/<string:name>/images/iscsi/<string:version>', methods=['PUT'], defaults={'kernel_name': None})
def new_image(name, kernel_name, version):
    farm = models.Farm.query.filter(models.Farm.name==name).first_or_404()
    form = forms.BootImageForm()

    if form.validate_on_submit():

        _version = secure_filename(version)

        if kernel_name:
            image_cls = models.PxeBootImage
            images_store = pxe_images_store

            kernel = Kernel.query.get(kernel_name)
            if not kernel:
                return 'Unknown kernel: %s' % kernel_name, 404

        else:
            image_cls = models.IscsiBootImage
            images_store = iscsi_images_store

        image = image_cls.query.filter(image_cls.farm==farm, image_cls.version==_version).first()

        if image:
            return 'Version %s of image for farm %s already exist!' % (_version, farm.name), 400

        image = image_cls(farm, _version)

        if kernel_name:
            image.kernel = kernel

        db.session.add(image)

        filename = images_store.save(form.image.data, folder=str(farm.id), name=image.filename)

        events.PyBootstrapperEventFilesNewImage.register(version, farm)

        db.session.commit()
        return filename, 201

    else:
        current_app.logger.error(form.errors)
        return 'Form data is invalid: %s' % form.errors, 400


@mod.route('/<string:name>', methods=['GET', 'POST'])
@mod.route('/_new_', methods=['GET', 'POST'], defaults={'name': None})
def farm(name):

    farm = None
    kernels = None
    code = 200

    if name:
        farm = models.Farm.query.filter(models.Farm.name==name).first_or_404()
        kernels = Kernel.query.all()

    form = forms.FarmForm(obj=farm)

    if form.validate_on_submit():
        if not farm:
            farm = models.Farm()
            db.session.add(farm)
            code = 201

        form.populate_obj(farm)
        db.session.commit()

    else:
        code = 400
        current_app.logger.error(form.errors)

    return render_template("farms/farm.html",
                           farm=farm, form=form,
                           kernels=kernels), code
