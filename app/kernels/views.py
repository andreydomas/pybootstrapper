from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app

from app.ext import db, kernels_store
import models
import forms

mod = Blueprint('kernels', __name__, url_prefix='/kernels')

@mod.route('/', methods=['GET'])
def list():
    kernels = models.Kernel.query.all()
    return render_template("kernels/list.html", kernels=kernels)


@mod.route('/<string:name>', methods=['POST'])
def new_kernel(name):
    form = forms.KernelForm()

    if form.validate_on_submit():

        if models.Kernel.query.get(name):
            return 'Version %s of image for farm %s already exist!' % (version, farm.name), 400

        kernel = models.Kernel(name)

        db.session.add(kernel)

        filename = kernels_store.save(form.kernel.data, name=kernel.name)

        db.session.commit()

        return filename, 201

    else:
        current_app.logger.error(form.errors)
        return 'Form data is invalid', 400
