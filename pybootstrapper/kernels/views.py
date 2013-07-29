from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app
from werkzeug import secure_filename

from pybootstrapper.ext import db, kernels_store
from pybootstrapper import events
import models
import forms

mod = Blueprint('kernels', __name__, url_prefix='/kernels')

@mod.route('/', methods=['GET'])
def list():
    kernels = models.Kernel.query.options(
                db.undefer('boot_images_count')
            ).paginate(int(request.args.get('p', 1)))
    return render_template("kernels/list.html", kernels=kernels)


@mod.route('/_add_', methods=['GET', 'POST'], defaults={'name': None})
@mod.route('/<string:name>', methods=['PUT'])
def add(name):
    form = forms.KernelForm()

    if request.method == 'PUT':
        form.name.data = name

    if form.validate_on_submit():

        _name = secure_filename(form.name.data)

        kernel = models.Kernel(_name)

        db.session.add(kernel)

        filename = kernels_store.save(form.kernel.data, name=kernel.name)

        events.PyBootstrapperEventFilesNewKernel.register(kernel.name)

        db.session.commit()

        if request.method == 'PUT':
            return filename, 201
        else:
            return redirect(url_for('.list'))

    else:
        if form.errors:
            current_app.logger.error(form.errors)

        if request.method == 'PUT':
            return 'Form data is invalid', 400

    return render_template('kernels/add.html', form=form), 400 if form.errors else 200
