""" Provide an environment for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


from .template import Template
from .scope import Scope
from .loaders import FileSystemLoader
from .errors import *

from .lib import StdLib

class Environment(object):
    """ represent a template environment. """

    def __init__(self, context=None, loader=None, importers=None):
        """ Initialize the template environment. """

        self._scope = Scope()
        self._scope_stack = [self._scope]
        self._importers = { "mrbavii_lib_template.stdlib": StdLib }
        self._imported = {}

        if context:
            self._scope._local.update(context)

        if loader:
            self._loader = loader
        else:
            self._loader = FileSystemLoader()

        if importers:
            self._importers.update(importers)

    def load_file(self, filename, parent=None):
        """ Load a template from a file. """
        return self._loader.load_template(self, filename, parent)

    def _push_scope(self, template=False):
        """ Create a new scope. """
        self._scope = Scope(self._scope, template)
        self._scope_stack.append(self._scope)

        return self._scope

    def _pop_scope(self):
        """ Pop a scope off the stack. """
        self._scope_stack.pop()
        self._scope = self._scope_stack[-1]

    def set(self, name, value, where=Scope.SCOPE_LOCAL):
        """ Set a value in the a scope. """
        if where == Scope.SCOPE_LOCAL:
            self._scope._local[name] = value
        elif where == Scope.SCOPE_GLOBAL:
            self._scope._global[name] = value
        elif where == Scope.SCOPE_TEMPLATE:
            self._scope._template[name] = value
        elif where == Scope.SCOPE_PRIVATE:
            self._scope._private[name] = value
        else:
            # Shold never happen, but default to local
            self._scope._local[name] = value

    def update(self, values):
        """ Update values in the context. """
        self._scope._local.update(values)

    def unset(self, name):
        """ Unset a variable from the current scope. """
        self._scope._local.pop(name, None)
        self._scope._private.pop(name, None)

    def clear(self):
        """ Clear the current context. """
        self._scope._local.clear()
        self._scope._private.clear()

    def get(self, var):
        """ Get a dotted variable. """

        # Find the scope dict it is in
        first = True
        for entry in reversed(self._scope_stack):
            if first:
                first = False
                # Try private scope first
                scope = entry._private
                if var[0] in scope:
                    break

            scope = entry._local
            if var[0] in scope:
                break
        else:
            raise KeyError(var[0])

        # Solve dotted variables
        value = scope[var[0]]
        for dot in var[1:]:
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

    def load_import(self, name):
        """ Load a lib from an importer. """

        if not name in self._imported:
            if not name in self._importers:
                raise KeyError(name)

            self._imported[name] = self._importers[name]()

        return self._imported[name]


