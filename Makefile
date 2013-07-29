ENV := ./env
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
	${PIP} install -U \
			setuptools \
			Flask \
			flask-debugtoolbar \
			blinker \
			Flask-SQLAlchemy \
			Flask-Script \
			Flask-WTF \
			Flask-Uploads \
			netaddr \
			pyping \
			tornado\>=3.1

db: drop_db
	${PYTHON} manager.py sync_db

drop_db:
	${PYTHON} manager.py drop_db

fixtures: db
	${PYTHON} manager.py fixtures

tests:
	${NOSETESTS} -vs tests

dist:
	${PYTHON} setup.py sdist --formats=gztar

.PHONY: fixtures tests dist env
