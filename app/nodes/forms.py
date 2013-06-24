from netaddr import IPAddress, IPNetwork
from flask.ext.wtf import Form, TextField, DataRequired, ValidationError, QuerySelectField

from ..misc.validators import form_ip_validator, form_net_validator, form_mac_validator
from ..pools.models import Pool

def str2ip(s):
    return IPAddress(str(s)) if s else None

class NodeForm(Form):
    id = TextField('MAC',
            validators=[DataRequired(), form_mac_validator]
            )

    pool = QuerySelectField('Pool',
            query_factory=lambda: Pool.query.all(),
            validators=[form_net_validator],
            )

    static_ip = TextField('Static IP address',
            validators=[form_ip_validator],
            filters=[str2ip]
            )

    boot_image = QuerySelectField('Image version',
                            get_pk=lambda image: image.version,
                            allow_blank=True
                        )
