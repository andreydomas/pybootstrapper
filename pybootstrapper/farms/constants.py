from collections import namedtuple


# look at methods in PyBootstrapperEvent model
_types =('PXE', 'ISCSI')

images_types = namedtuple('PybootstrapperImagesTypes', _types)(*_types)
