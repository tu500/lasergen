import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'LaserGen',
    version = '0.1',
    author = 'Philip Matura',
    author_email = 'philip.m@tura-home.de',
    url = 'https://github.com/tu500/lasergen',
    description = (
            'LaserGen is an extendable python library / framework for '
            'automatically creating designs to be used with laser cutters to '
            'create simple to complex boxed cases.'
        ),
    packages = ['lasergen'],
    long_description = read('Readme.md'),
    install_requires = ['numpy', 'svgpathtools'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
    ],
)
