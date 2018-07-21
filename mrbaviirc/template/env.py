""" Provide an environment for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


from .template import Template
from .scope import Scope
from .loaders import UnrestrictedLoader
from .errors import *

from .lib import StdLib

class Environment(object):
    """ represent a template environment. """

    def __init__(self, loader=None, importers=None):
        """ Initialize the template environment. """

        self._importers = { "mrbaviirc.template.stdlib": StdLib }
        self._imported = {}
        self._code_enabled = False

        if loader:
            self._loader = loader
        else:
            self._loader = UnrestrictedLoader()

        if importers:
            self._importers.update(importers)

    def register_importer(self, name, importer):
        """ Register an importer """
        self._importers[name] = importer

    def enable_code(self, enabled=True):
        """ Enable use of the code tag in templates. """
        self._code_enabled = enabled

    def load_file(self, filename, parent=None):
        """ Load a template from a file. """
        return self._loader.load_template(self, filename, parent)

    def load_import(self, name):
        """ Load a lib from an importer. """

        if not name in self._imported:
            if not name in self._importers:
                raise KeyError(name)

            self._imported[name] = self._importers[name]()

        return self._imported[name]


