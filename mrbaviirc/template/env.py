""" Provide an environment for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


from .template import Template
from .loaders import FileSystemLoader
from .errors import *


class Environment(object):
    """ represent a template environment. """

    def __init__(self, context=None, loader=None):
        """ Initialize the template environment. """

        self._context = {}
        if context:
            self._context.update(context)

        if loader:
            self._loader = loader
        else:
            self._loader = FileSystemLoader()

        self._saved_contexts = []

    def load_file(self, filename, parent=None):
        """ Load a template from a file. """
        return self._loader.load_template(self, filename, parent)

    def load_text(self, text):
        """ Load a template from a string. """
        return Template(self, text=text)

    def save_context(self):
        """ Save the current context. """
        self._saved_contexts.append(dict(self._context))

    def restore_context(self):
        """ Restore a saved context. """
        self._context = self._saved_contexts.pop()

    def get(self, var):
        """ Evaluate dotted expressions. """
        value = self._context
        for dot in var:
            value = value[dot]
                
        return value

    def set(self, name, value):
        """ Set a value in the context. """
        self._context[name] = value


