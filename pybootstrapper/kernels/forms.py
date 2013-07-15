from flask.ext.wtf import Form, FileField, TextField, file_allowed, file_required, DataRequired, ValidationError
from werkzeug import secure_filename

from pybootstrapper.ext import kernels_store
import models

class KernelForm(Form):
    name = TextField('Name', validators=[DataRequired()])
    kernel =FileField('Kernel', validators=[file_required(), file_allowed(kernels_store)])

    def validate_name(form, field):
        if field.data:
            _name = secure_filename(field.data)
            if models.Kernel.query.get(_name):
                raise ValidationError('Kernel %s already exist!' % field.data)
