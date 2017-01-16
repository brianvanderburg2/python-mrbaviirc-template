""" Provide a scope to hold variables. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


class Scope(object):
    """ Represent the different variable levels at the current scope. """
    SCOPE_LOCAL = 0
    SCOPE_GLOBAL = 1
    SCOPE_TEMPLATE = 2
    SCOPE_PRIVATE = 3

    def __init__(self, parent=None, template=False):
        """ Initialize the current scope. """

        # We always have the local scope variables
        self._local = {}

        # Private variables can only be accessed from the scope that set them
        self._private = {}

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

