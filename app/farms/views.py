from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app

from app.ext import db, images_store
from ..pools.models import Pool

import models
import forms

mod = Blueprint('farms', __name__, url_prefix='/farms')

@mod.route('/', methods=['GET'])
def list():
    farms = models.Farm.query.all()
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
        images = models.BootImage.query.all()

    return render_template("farms/images.html", images=images, caption=caption)


@mod.route('/<string:name>/images/<string:version>', methods=['POST'])
def new_image(name, version):
    farm = models.Farm.query.filter(models.Farm.name==name).first_or_404()
    form = forms.BootImageForm()

    if form.validate_on_submit():

        image = models.BootImage.query.filter(models.BootImage.farm==farm, models.BootImage.version==version).first()
        if image:
            return 'Version %s of image for farm %s already exist!' % (version, farm.name), 400

        image = models.BootImage(farm, version, form.kernel.data)

        db.session.add(image)

        filename = images_store.save(form.image.data, folder=str(farm.id), name=image.filename)

        db.session.commit()

        return filename, 201

    else:
        current_app.logger.error(form.errors)
        return 'Form data is invalid', 400


@mod.route('/<string:name>', methods=['GET', 'POST'])
@mod.route('/new', methods=['GET', 'POST'], defaults={'name': None})
def farm(name):

    farm = None
    code = 200

    if name:
        farm = models.Farm.query.filter(models.Farm.name==name).first_or_404()

    if request.method == 'POST':

        form = forms.FarmForm()
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

    else:
        form = forms.FarmForm(obj=farm)

    return render_template("farms/farm.html", farm=farm, form=form), code
