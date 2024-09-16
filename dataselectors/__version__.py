__author__ = 'Robbert Harms'
__date__ = '2024-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'


from importlib import metadata
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import tomllib

try:
    __version__ = metadata.version('dataselectors')
except PackageNotFoundError:
    with open(Path(__file__).parent.parent / 'pyproject.toml', 'rb') as f:
        pyproject = tomllib.load(f)
        __version__ = pyproject['project']['version']
