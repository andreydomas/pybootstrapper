from netaddr import IPAddress
from flask.ext.wtf import Form, html5, TextField, DataRequired, ValidationError, validators

from ..misc.validators import form_ip_validator, form_net_validator, form_mac_validator

def str2ip(s):
    return IPAddress(s) if s else None

class NodeForm(Form):
    id = TextField('MAC', validators=[DataRequired(), form_mac_validator])
    static_ip = TextField('Static IP address', validators=[form_ip_validator], filters=(str2ip,))

