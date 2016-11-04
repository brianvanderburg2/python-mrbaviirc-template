""" Provide a simple template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

from ._version import __version__


from .errors import *
from .renderers import *
from .env import Environment
from .loaders import *
from .template import Template
from .lib import Library, StdLib


