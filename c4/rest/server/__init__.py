"""
REST server implementation
"""
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

from .tornadoserver import (BaseRequestHandler,
                            RestServerProcess,
                            getRouteMap,
                            route)

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
