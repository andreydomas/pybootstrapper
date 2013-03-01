import sqlalchemy.types as types


from netaddr import IPAddress
class Ip(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if value is not None:
            return int(IPAddress(value))

    def process_result_value(self, value, dialect):
        if value is not None:
            return IPAddress(value)


from netaddr import EUI
class Mac(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if value is not None:
            return int(EUI(value))

    def process_result_value(self, value, dialect):
        if value is not None:
            return EUI(value)


from netaddr import IPNetwork
class Subnet(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(IPNetwork(value))

    def process_result_value(self, value, dialect):
        if value is not None:
            return IPNetwork(value)
