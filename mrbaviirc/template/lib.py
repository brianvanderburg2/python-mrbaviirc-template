""" The module provides library functions to the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


class Library(object):
    """ Represent a library of functions. """

    def __init__(self):
        """ Initialize the library. """
        pass

    def __getitem__(self, name):
        """ Get an item. """
        try:
            return getattr(self, "lib_" + name)
        except AttributeError:
            raise KeyError(name)


class StdLib(Library):
    """ Represent the top-level standard library. """

    def __init__(self):
        """ Initialize the standard library. """
        self._indent = None

    def lib_str(self, value):
        """ Return the string of an value. """
        return str(value)

    def lib_int(self, value):
        """ Return the interger of a value. """
        return int(value)

    def lib_count(self, value):
        """ Return how many things are in a value. """
        return len(value)

    def lib_add(self, value1, value2):
        """ Add two values. """
        return value1 + value2

    def lib_sub(self, value1, value2):
        """ Subtract two values. """
        return value1 - value2

    def lib_mul(self, value1, value2):
        """ Multiply two values """
        return value1 * value2

    def lib_div(self, value1, value2):
        """ Divide two values """
        return value1 / value2

    def lib_mod(self, value1, value2):
        """ Take the remainder of division. """
        return value1 % value2

    def lib_iseven(self, value):
        """ Determine if a value is even. """
        return (value % 2) == 0

    def lib_isodd(self, value):
        """ Determine if a value is odd. """
        return (value % 2) == 1

    def lib_eq(self, value1, value2):
        """ Determine if two values are equal. """
        return value1 == value2

    def lib_ne(self, value1, value2):
        """ Determine if two values are not equal. """
        return value1 != value2

    def lib_concat(self, *values):
        """ Concatenate values. """
        return "".join(values)


