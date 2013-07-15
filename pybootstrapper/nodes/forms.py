from netaddr import IPAddress, IPNetwork
from flask.ext.wtf import Form, TextField, DataRequired, ValidationError, QuerySelectField

from ..misc.validators import form_ip_validator, form_net_validator, form_mac_validator
from ..pools.models import Pool
from pybootstrapper.ext import db

def str2ip(s):
    return IPAddress(str(s)) if s else None

class NodeForm(Form):
    id = TextField('MAC',
            validators=[DataRequired(), form_mac_validator]
            )

    hostname = TextField('Hostname',
            validators=[DataRequired()]
            )


    pool = QuerySelectField('Pool',
            query_factory=lambda: Pool.query.all(),
            )

    static_ip = TextField('Static IP address',
            validators=[form_ip_validator],
            filters=[str2ip]
            )

    boot_image = QuerySelectField('Image version', allow_blank=True)
