import re
from flask.ext.wtf import Form, TextField, DataRequired, FileField, QuerySelectField, file_allowed, file_required

from ..kernels.models import Kernel
from pybootstrapper.ext import pxe_images_store


class FarmForm(Form):

    name = TextField('Name', validators=[DataRequired(),])

    def validate_name(form, field):
        if field.data:
            field.data = re.sub(r'[^a-z0-9_.-]', '_', field.data)

class BootImageForm(Form):
    image = FileField('Boot image', validators=[file_required(), file_allowed(pxe_images_store)])
#    kernel = QuerySelectField('Kernel',
#                query_factory=lambda: Kernel.query.all(),
#                validators=[DataRequired(), ])
