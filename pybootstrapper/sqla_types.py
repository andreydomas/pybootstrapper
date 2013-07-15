import sqlalchemy.types as types


from netaddr import IPAddress
class Ip(types.TypeDecorator):
    impl = types.Integer

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            from sqlalchemy.dialects.mysql import INTEGER as Integer
        else:
            from sqlalchemy.types import Integer

        return dialect.type_descriptor(Integer(unsigned=True))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return int(IPAddress(value))

    def process_result_value(self, value, dialect):
        if value is not None:
            return IPAddress(value)


from netaddr import EUI
class Mac(types.TypeDecorator):
    impl = types.BigInteger

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            from sqlalchemy.dialects.mysql import BIGINT as BigInteger
        else:
            from sqlalchemy.types import BigInteger

        return dialect.type_descriptor(BigInteger(unsigned=True))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return int(EUI(value))

    def process_result_value(self, value, dialect):
        if value is not None:
            return EUI(value)


from netaddr import IPNetwork
class Subnet(types.TypeDecorator):
    impl = types.CHAR

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.CHAR(18))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(IPNetwork(value))

    def process_result_value(self, value, dialect):
        if value is not None:
            return IPNetwork(value)
