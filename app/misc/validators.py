from netaddr import IPAddress, IPNetwork, AddrFormatError

def form_ip_validator(form, field):
    try:
        IPAddress(field.data)
    except AddrFormatError:
        raise ValidationError('Invalid address')


def form_net_validator(form, field):
    try:
        IPNetwork(field.data)
    except AddrFormatError:
        raise ValidationError('Invalid network')
