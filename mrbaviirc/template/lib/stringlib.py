""" String library module. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016-2019"
__license__     = "Apache License 2.0"


class _StringLib(object):
    """ String based functions. """

    def concat(self, *values):
        """ Concatenate values. """
        return "".join(values)

    def split(self, delim, value):
        """ Split a value into parts. """
        return value.split(delim)

    def join(self, delim, values):
        """ Join a value from parts. """
        return delim.join(values)

    def replace(self, source, target, value):
        """ Replace all source with target in value. """
        return value.replace(source, target)

    def strip(self, value, what=None):
        """ Strip from the start and end of value. """
        return value.strip(what)

    def rstrip(self, value, what=None):
        """ Strip from the end of value. """
        return value.rstrip(what)

    def lstrip(self, value, what=None):
        """ Strip from the start of value. """
        return value.lstrip(what)


FACTORY = _StringLib
