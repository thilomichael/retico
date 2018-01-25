#!/usr/bin/env python3

"""
Setup script.

Use this script to install the simulation framework. Usage:
    $ python3 setup.py install
The run the simulation:
    $ retico [-h]
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'A RealTimeConversation Framework',
    'author': 'Thilo Michael',
    'url': '??',
    'download_url': '??',
    'author_email': 'thilo.michael@tu-berlin.de',
    'version': '0.1',
    'install_requires': ['pyaudio', 'google-cloud-speech'],
    'packages': ["rtcmodules", "system"],
    'entry_points': {
        'console_scripts': [
            'retico=system.retico:main',
        ],
    },
    'name': 'ReTiCo',
}

setup(**config)
