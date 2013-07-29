import sys
import os
from setuptools import setup, find_packages
from subprocess import call

setup(
    name='pybootstrapper',
    version='1.0',
    packages=find_packages(),
    platforms='any',
    install_requires=[
            'setuptools',
            'tornado>=3.1',
            'Flask>=0.10.1',
            'blinker',
            'sqlalchemy>=0.8',
            'Flask-SQLAlchemy>=0.16',
            'Flask-WTF>=0.8.3',
            'Flask-Uploads',
            'netaddr',
            'pyping'
        ],
    scripts = ['scripts/pybootstrapper_daemons'],
    include_package_data=True
)
