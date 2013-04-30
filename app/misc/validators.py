from flask.ext.wtf import ValidationError
from netaddr import IPAddress, IPNetwork, EUI, AddrFormatError


def form_ip_validator(form, field):
    if field.data:
        try:
            IPAddress(str(field.data))
        except AddrFormatError:
            raise ValidationError('Invalid IP')


def form_mac_validator(form, field):
    if field.data:
        try:
            EUI(str(field.data))
        except AddrFormatError:
            raise ValidationError('Invalid MAC')


def form_net_validator(form, field):
    if field.data:
        try:
            IPNetwork(str(field.data))
        except AddrFormatError:
            raise ValidationError('Invalid network')
