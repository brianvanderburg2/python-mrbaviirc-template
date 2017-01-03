""" Provide an environment for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


from .template import Template
from .loaders import FileSystemLoader
from .errors import *

from .lib import StdLib

class Scope(object):
    """ Represent the different variable levels at the current scope. """

    def __init__(self, parent=None, template=False):
        """ Initialize the current scope. """

        # We always have the local scope variables
        self._local = {}

        # Set global and template
        if parent:
            self._global = parent._global

            if template:
                # We are starting a template scope
                self._template = self._local
            else:
                self._template = parent._template
        else:
            self._global = self._local
            self._template = self._local


class Environment(object):
    """ represent a template environment. """

    def __init__(self, context=None, loader=None, callbacks=None, importers=None):
        """ Initialize the template environment. """

        self._scope = Scope()
        self._scope_stack = [self._scope]
        self._callbacks = {}
        self._importers = { "mrbavii_lib_template.stdlib": StdLib }
        self._imported = {}

        if context:
            self._scope._local.update(context)

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
        self._scope = Scope(self._scope)
        self._scope_stack.append(self._scope)

        return self._scope

    def _pop_scope(self):
        """ Pop a scope off the stack. """
        self._scope_stack.pop()
        self._scope = self._scope_stack[-1]

    def set(self, name, value, where=0):
        """ Set a value in the a scope. """
        if where == 0:
            self._scope._local[name] = value
        elif where == 1:
            self._scope._global[name] = value
        else:
            self._scope._template[name] = value

    def update(self, values):
        """ Update values in the context. """
        self._scope._local.update(values)

    def clear(self):
        """ Clear the current context. """
        self._scope._local.clear()

    def get(self, var):
        """ Get a dotted variable. """
        for entry in reversed(self._scope_stack):
            scope = entry._local

            if not var[0] in scope:
                continue

            value = scope
            for dot in var:
                # Return an attribute directly (can be used to return functions)
                attr = "lib_" + dot
                if hasattr(value, attr):
                    value = getattr(value, attr)
                    continue

                # Call a function and return the value
                attr = "call_" + dot
                if hasattr(value, attr):
                    value = getattr(value, attr)()
                    continue

                # Try to acess the item directly
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


