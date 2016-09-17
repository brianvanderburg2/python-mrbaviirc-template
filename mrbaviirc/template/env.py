""" Provide an environment for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


from .template import Template
from .loaders import FileSystemLoader
from .errors import *


class Scope(object):
    """ Represent a scope of variables. """

    def __init__(self, parent=None):
        """ Initialize our scope. """
        self._context = {}
        self._scope = [self._context]
        if parent:
            self._scope.extend(parent._scope)

    def create(self):
        """ Create a child scope. """
        return Scope(self)

    def set(self, name, value):
        """ Set a value in the context. """
        self._context[name] = value

    def update(self, values):
        """ Update values in the context. """
        self._context.update(values)

    def clear(self):
        """ Clear the current context. """
        self._context.clear()

    def get(self, var):
        """ Get a dotted variable. """
        for context in self._scope:
            if not var[0] in context:
                continue

            value = context
            for dot in var:
                value = value[dot]

            return value

        raise KeyError(var[0])


class Environment(object):
    """ represent a template environment. """

    def __init__(self, context=None, loader=None):
        """ Initialize the template environment. """

        self._scope = Scope()
        if context:
            self._scope.update(context)

        if loader:
            self._loader = loader
        else:
            self._loader = FileSystemLoader()

    def load_file(self, filename, parent=None):
        """ Load a template from a file. """
        return self._loader.load_template(self, filename, parent)

    def load_text(self, text):
        """ Load a template from a string. """
        return Template(self, text=text)

    def get_scope(self):
        """ Return the scope. """
        return self._scope

