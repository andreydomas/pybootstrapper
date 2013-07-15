import random
from netaddr import EUI, IPAddress, IPNetwork
import yaml
import sys
from datetime import datetime, timedelta

r = []


def random_date(start=datetime.strptime('1/1/2008 1:30 PM', '%m/%d/%Y %I:%M %p'), end=datetime.strptime('12/31/2012 4:50 AM', '%m/%d/%Y %I:%M %p')):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return (start + timedelta(seconds=random_second))

id = random.getrandbits(64)

for i in range(1, 512):

    d = {
      'created': random_date(),
      'id': str(EUI(id)),
      'hostname': 'node%d' % i,
      'pool_subnet': random.choice(['192.168.0.0/25', '192.168.0.129/25', '192.168.56.0/24', '10.0.0.0/8', '172.16.0.0/16'])
    }

    id = id + 1

    if random.randint(0,10) / 5:
        d['static_ip'] = str(IPNetwork(d['pool_subnet'])[random.randint(2, 120)])

    r.append(d)

yaml.dump_all(r, sys.stdout, default_flow_style=False)
