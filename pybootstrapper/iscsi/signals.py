from blinker import Namespace

iscsi_signals = Namespace()

create = iscsi_signals.signal('create')
delete = iscsi_signals.signal('delete')
