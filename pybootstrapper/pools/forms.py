import re
from flask.ext.wtf import Form, TextField, DataRequired, ValidationError, validators, widgets, Field, QuerySelectField

from ..misc.validators import form_ip_validator, form_net_validator
from ..dhcp.pydhcplib.dhcp_constants import DhcpOptionsList
from ..farms.models import Farm
import models

class OptionsField(Field):
    widget = widgets.TextArea()

    def _value(self):
        if self.data:
            return '\n'.join(map(lambda option: str(option), self.data))
        else:
            return ""

    def process_formdata(self, value):
        if value:
            self.data = []
            for line in value[0].splitlines():
                if line:
                    option, value = line.split('=')
                    option_obj = models.PoolOption(option.strip(), value.strip())
                    self.data.append(option_obj)


class PoolForm(Form):
    name = TextField('Name')
    subnet = TextField('Subnet', validators=[DataRequired(), form_net_validator])
    farm = QuerySelectField('Farm', query_factory=lambda: Farm.query.all(), validators=[DataRequired()])

    options = OptionsField('Options', default=[
                        models.PoolOption('router', ''),
                        models.PoolOption('domain_name_server', '')
                    ])

    def validate_options(form, field):
        if field.data:
            for opt in field.data:
                try:
                    opt.binary
                except KeyError:
                    raise ValidationError('Bad type "%s"' % opt._option)
                except IndexError:
                    raise ValidationError('Bad option name "%s"' % opt._option)
