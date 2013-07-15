from collections import namedtuple


# look at methods in PyBootstrapperEvent model
_types =('base',
         'dhcp_unknown_host',
         'dhcp_leasing',
         'files_new_image',
         'files_new_kernel'
        )

types = namedtuple('PybootstrapperEventTypes', _types)(*_types)
