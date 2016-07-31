""" Provide an environment for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import os

from .template import Template
from .errors import *


class Environment(object):
    """ represent a template environment. """

    def __init__(self, context=None):
        """ Initialize the template environment. """

        self._context = {}
        if context:
            self._context.update(context)

        self._saved_contexts = []
        self._cache = {}

    def load_file(self, filename):
        """ Load a template from a file. """

        abspath = os.path.abspath(os.path.normpath(filename))
        if not abspath in self._cache:
            self._cache[abspath] = Template(self, filename=abspath)

        return self._cache[abspath]

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

    def set(self, var1, var2):
        """ Set a value in the context. """
        self._context[var1] = var2




