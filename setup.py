#!/usr/bin/env python3

"""
Setup script.

Use this script to install the simulation framework. Usage:
    $ python3 setup.py install
The run the simulation:
    $ retico [-h]
"""

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

config = {
    'description': 'A RealTimeConversation Framework',
    'author': 'Thilo Michael',
    'url': '??',
    'download_url': '??',
    'author_email': 'thilo.michael@tu-berlin.de',
    'version': '0.1',
    'install_requires': ['pyaudio', 'pySDL2', 'kivy'],
    'packages': find_packages(),
    'entry_points': {
        'console_scripts': [
            'retico-builder=retico_builder.builder:main',
        ],
    },
    'name': 'ReTiCo',
}

setup(**config)
