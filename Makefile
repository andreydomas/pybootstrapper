ENV := /var/tmp/pybootstrapper
PYTHON := ${ENV}/bin/python
IPYTHON := ${ENV}/bin/ipython
PIP :=  ${ENV}/bin/pip
NOSETESTS := ${ENV}/bin/nosetests

web:
	${PYTHON} manager.py runserver -t 0.0.0.0

dhcp:
	${PYTHON} manager.py dhcp

tftp:
	${PYTHON} manager.py tftp

shell:
	${PYTHON} manager.py shell

env:
	virtualenv --system-site-packages ${ENV}
	${PIP} install -U Flask
	${PIP} install -U Flask-SQLAlchemy
	${PIP} install -U Flask-Script
	${PIP} install -U Flask-WTF
	${PIP} install -U Flask-Uploads
	${PIP} install -U netaddr
	${PIP} install -U pyping
	${PIP} install -U tftpy

db: drop_db
	${PYTHON} manager.py sync_db

drop_db:
	${PYTHON} manager.py drop_db

fixtures: db
	${PYTHON} manager.py fixtures

tests:
	${NOSETESTS} -vs tests

.PHONY: fixtures tests
