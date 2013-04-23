from flask.ext.wtf import Form, html5, TextField, DataRequired, ValidationError, validators

from ..misc.validators import form_ip_validator, form_net_validator

class NodeForm(Form):
    id = TextField('MAC', validators=[DataRequired()])

    static_ip = TextField('Static IP address', validators=[DataRequired(), form_ip_validator])

