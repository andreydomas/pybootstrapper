from flask.ext.wtf import Form, html5, TextField, DataRequired, ValidationError, validators

from ..misc.validators import form_ip_validator, form_net_validator

class PoolForm(Form):
    subnet = TextField('Subnet', validators=[DataRequired(), form_net_validator])

    router = TextField('Gateway', validators=[DataRequired(), form_ip_validator])

    domain = TextField('Domain',
                validators=[DataRequired(), validators.Length(max=253, message='Too long')])

    time_offset = html5.IntegerField('Time offset(from UTC)')

    lease_time = html5.IntegerField('Lease time', validators=[DataRequired()])
