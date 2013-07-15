import logging
from datetime import datetime

logger = logging.getLogger('fixtures')

class Fixtured:
    @classmethod
    def from_yaml(cls, data):
        model_obj = cls()

        for key, value in data.items():
            try:
                setattr(model_obj, key, value)
            except AttributeError, e:
                logger.error('%s: %s -> %s', e, key, value)
        return model_obj
