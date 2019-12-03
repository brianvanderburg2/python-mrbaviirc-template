""" Utility functionsTokenize the input."""
# pylint: disable=too-few-public-methods,too-many-branches,too-many-statements

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"

__all__ = ["specialfunction", "DictToAttr"]


class specialfunction:
    """ A base class for a sepcial special function which receives expression nodes. """

    def __init__(self):
        """ Initialize  the function. """
        pass

    def __call__(self, state, params):
        """ Call the special function. """
        return None


class DictToAttr(dict):
    """ Make dictionary items accessible as attributes. """

    def __getattr__(self, name):
        return self[name]
