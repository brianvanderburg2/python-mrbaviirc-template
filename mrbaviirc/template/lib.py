""" The module provides library functions to the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import os


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


class _PathLib(Library):
    """ Path based functions. """

    def __init__(self):
        """ Initialize the library. """
        pass

    lib_sep = os.sep
    """ The path separator for the current platform. """

    def lib_join(self, *parts):
        """ Join a path. """
        return os.path.join(*parts)

    def lib_split(self, path):
        """ Split a path into a head and a tail. """
        return os.path.split(path)

    def lib_splitext(self, path):
        """ Split the extension out of the path. """
        return os.path.splitext(path)

    def lib_dirname(self, path):
        """ Return the directory name of a path. """
        return os.path.dirname(path)

    def lib_basename(self, path):
        """ Return the base name of a path. """
        return os.path.basename(path)

    def lib_relpath(self, target, fromdir):
        """ Return a relative path to target from the directory fromdir. """
        return os.path.relpath(target, fromdir)


class StdLib(Library):
    """ Represent the top-level standard library. """

    def __init__(self):
        """ Initialize the standard library. """
        self._path = None

    @property
    def lib_path(self):
        """ Return the path library. """
        if self._path is None:
            self._path = _PathLib()

        return self._path

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

    def lib_split(self, delim, value):
        """ Split a value into parts. """
        return value.split(delim)

    def lib_join(self, delim, values):
        """ Join a value from parts. """
        return delim.join(values)

    def lib_replace(self, source, target, value):
        """ Replace all source with target in value. """
        return value.replace(source, target)

    def lib_strip(self, value, what=None):
        """ Strip from the start and end of value. """
        return value.strip(what)

    def lib_rstrip(self, value, what=None):
        """ Strip from the end of value. """
        return value.rstrip(what)

    def lib_lstrip(self, value, what=None):
        """ Strip from the start of value. """
        return value.lstrip(what)

