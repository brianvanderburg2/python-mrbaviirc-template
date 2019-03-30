""" Provide an environment for templates. """
# pylint: disable=too-many-arguments

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"

__all__ = ["Environment"]


import threading


from .template import Template
from .loaders import UnrestrictedLoader

from .lib import StdLib

class Environment(object):
    """ represent a template environment. """

    def __init__(self, loader=None, importers=None, allow_code=False):
        """ Initialize the template environment. """

        self.importers = {"mrbaviirc.template.stdlib": StdLib}
        self.imported = {}
        self.hooks = {}
        self.code_enabled = allow_code
        self.lock = threading.Lock()

        if loader:
            self.loader = loader
        else:
            self.loader = UnrestrictedLoader()

        if importers:
            self.importers.update(importers)

    def register_importer(self, name, importer):
        """ Register an importer """
        self.importers[name] = importer

    def register_hook(self, name, callback):
        """ Register a hook. """
        self.hooks.setdefault(name, []).append(callback)

    def allow_code(self, enabled=True):
        """ Enable use of the code tag in templates. """
        self.code_enabled = enabled

    def load_file(self, filename, parent=None):
        """ Load a template from a file. """
        return self.loader.load_template(self, filename, parent)

    def load_text(self, text, filename="", allow_code=False):
        """ Load a template direct from text. """
        template = Template(self, text, filename, allow_code)
        self.loader.fix_load_text(template)
        return template

    def load_import(self, name):
        """ Load a lib from an importer. """

        with self.lock:
            if not name in self.imported:
                if not name in self.importers:
                    raise KeyError(name)

                self.imported[name] = self.importers[name]()

            return self.imported[name]

    def call_hook(self, hook, template, renderer, scope, params, reverse):
        """ Call a hook if it exist, otherwise just return. """

        callbacks = self.hooks.get(hook, None)
        if callbacks is None:
            return

        if reverse:
            for callback in reversed(callbacks):
                callback(self, template, renderer, scope, params)
        else:
            for callback in callbacks:
                callback(self, template, renderer, scope, params)
