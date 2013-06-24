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
            'tornado',
            'Flask>=0.9',
            'sqlalchemy>=0.8',
            'Flask-SQLAlchemy>=0.16',
            'Flask-WTF>=0.8.3',
        ],
    include_package_data=True
)
