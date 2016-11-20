""" Provide an environment for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


from .template import Template
from .loaders import FileSystemLoader
from .errors import *

from .lib import StdLib


class Environment(object):
    """ represent a template environment. """

    def __init__(self, context=None, loader=None, callbacks=None, importers=None):
        """ Initialize the template environment. """

        self._top = {}
        self._scope = self._top
        self._scope_stack = [self._top]
        self._callbacks = {}
        self._importers = { "mrbavii_lib_template.stdlib": StdLib }
        self._imported = {}

        if context:
            self._scope.update(context)

        if loader:
            self._loader = loader
        else:
            self._loader = FileSystemLoader()

        if callbacks:
            self._callbacks.update(callbacks)

        if importers:
            self._importers.update(importers)

    def load_file(self, filename, parent=None):
        """ Load a template from a file. """
        return self._loader.load_template(self, filename, parent)

    def load_text(self, text):
        """ Load a template from a string. """
        return Template(self, text=text)

    def _push_scope(self):
        """ Create a new scope. """
        self._scope = {}
        self._scope_stack.append(self._scope)

        return self._scope

    def _pop_scope(self):
        """ Pop a scope off the stack. """
        self._scope_stack.pop()
        self._scope = self._scope_stack[-1]

    def set(self, name, value, glbl=False):
        """ Set a value in the current scope. """
        if glbl:
            self._top[name] = value
        else:
            self._scope[name] = value

    def update(self, values):
        """ Update values in the context. """
        self._scope.update(values)

    def clear(self):
        """ Clear the current context. """
        self._scope.clear()

    def get(self, var):
        """ Get a dotted variable. """
        for scope in reversed(self._scope_stack):
            if not var[0] in scope:
                continue

            value = scope
            for dot in var:
                try:
                    value = value[dot]
                except:
                    raise KeyError(dot)

            return value

        raise KeyError(var[0])

    def load_import(self, name):
        """ Load a lib from an importer. """

        if not name in self._imported:
            if not name in self._importers:
                raise KeyError(name)

            self._imported[name] = self._importers[name]()

        return self._imported[name]


