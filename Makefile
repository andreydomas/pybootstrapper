ENV := /var/tmp/pybootstrapper
PYTHON := ${ENV}/bin/python
IPYTHON := ${ENV}/bin/ipython
PIP :=  ${ENV}/bin/pip
NOSETESTS := ${ENV}/bin/nosetests

run:
	${PYTHON} manager.py runserver

shell:
	${PYTHON} manager.py shell

env:
	virtualenv --system-site-packages ${ENV}
	${PIP} install twisted
	${PIP} install Flask
	${PIP} install Flask-SQLAlchemy
	${PIP} install Flask-Script
	${PIP} install netaddr
	${PIP} install pyping

db: drop_db
	${PYTHON} manager.py sync_db

drop_db:
	${PYTHON} manager.py drop_db

fixtures: db
	${PYTHON} manager.py fixtures

tests:
	${NOSETESTS} -vs tests

.PHONY: fixtures tests
