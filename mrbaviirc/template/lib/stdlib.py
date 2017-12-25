""" The module provides library functions to the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

__all__ = []
import os



class _PathLib(object):
    """ Path based functions. """

    @property
    def sep(self):
        """ The path separator for the current platform. """
        return os.sep

    def join(self, *parts):
        """ Join a path. """
        return os.path.join(*parts)

    def split(self, path):
        """ Split a path into a head and a tail. """
        return os.path.split(path)

    def splitext(self, path):
        """ Split the extension out of the path. """
        return os.path.splitext(path)

    def dirname(self, path):
        """ Return the directory name of a path. """
        return os.path.dirname(path)

    def basename(self, path):
        """ Return the base name of a path. """
        return os.path.basename(path)

    def relpath(self, target, fromdir):
        """ Return a relative path to target from the directory fromdir. """
        return os.path.relpath(target, fromdir)


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

    def substr(self, value, start, end=None):
        """ Get a substring from start up to but not including end. """
        if end is None:
            return value[start:]
        else:
            return value[start:end]

    def find(self, value, what, pos=None):
        """ Find a value, -1 if not found. """
        return value.find(what, pos)

    def rfind(self, value, what, pos=None):
        """ Find a vlue, -1 if not found. """
        return value.rfind(what, 0, pos)


class _ListLib(object):
    """ A library for dealing with lists. """

    def append(self, l, x):
        """ Append x to l """
        l.append(x)

    def extend(self, l, l2):
        """ Extend l with l2"""
        l.extend(l2)

    def insert(self, l, i, x):
        """ Insert x into l at a given position. """
        l.insert(i, x)

    def remove(self, l, x):
        """ Remove item the first item x from the list. """
        l.remove(x)

    def pop(self, l, i=-1):
        """ Pop and return an item. """
        return l.pop(i)

    def reverse(self, l):
        """ Return items in the list. """
        l.reverse()

    def count(self, l, x):
        """ Return the number of occurrences of x. """
        return l.count(x)

    def contains(self, l, x):
        """ Returns if the list contains x. """
        return x in l

    def splice(self, l, start, end):
        """ Return a sublist from start up to but not including end. """
        return l[start:end]


class _HtmlLib(object):
    """ An HTML library for escaping values. """

    def esc(self, value, quote=False):
        """ Escape for HTML. """
        return cgi.escape(value, quote)


class _IndentLib(object):
    """ Manage an indenter. """

    def __init__(self, indent):
        """ Initialize the indentor """
        super(_IndentLib, self).__init__()
        self._indent = str(indent)
        self._count = 0
        self._value = ""

    def more(self):
        """ Increase the indent. """
        self._count += 1
        self._value = self._indent * self._count
        return ""

    def less(self):
        """ Decrease the indent. """
        self._count -= 1
        self._value = self._indent * self._count
        return ""

    def __str__(self):
        """ Return the indent. """
        return self._value

__all__.append("StdLib")
class StdLib(object):
    """ Represent the top-level standard library. """

    def __init__(self):
        """ Initialize the standard library. """
        super(StdLib, self).__init__()
        self._path = None
        self._string = None
        self._list = None
        self._html = None

    @property
    def path(self):
        """ Return the path library. """
        if self._path is None:
            self._path = _PathLib()

        return self._path

    @property
    def string(self):
        """ Return the string library. """
        if self._string is None:
            self._string = _StringLib()

        return self._string

    @property
    def list(self):
        if self._list is None:
            self._list = _ListLib()

        return self._list

    @property
    def html(self):
        """ Return the HTML library. """
        if self._html is None:
            self._html = _HtmlLib()

        return self._html

    def indenter(self, indent):
        """ Return a new indenter. """
        return _IndentLib(indent)

    def str(self, value):
        """ Return the string of an value. """
        return str(value)

    def int(self, value):
        """ Return the interger of a value. """
        return int(value)

    def float(self, value):
        """ Return the float of a value. """
        return float(value)

    def count(self, value):
        """ Return how many things are in a value. """
        return len(value)

    def add(self, value1, value2):
        """ Add two values. """
        return value1 + value2

    def sub(self, value1, value2):
        """ Subtract two values. """
        return value1 - value2

    def mul(self, value1, value2):
        """ Multiply two values """
        return value1 * value2

    def div(self, value1, value2):
        """ Divide two values """
        return value1 / value2

    def mod(self, value1, value2):
        """ Take the remainder of division. """
        return value1 % value2

    def iseven(self, value):
        """ Determine if a value is even. """
        return (value % 2) == 0

    def isodd(self, value):
        """ Determine if a value is odd. """
        return (value % 2) == 1

    def eq(self, value1, value2):
        """ Determine if two values are equal. """
        return value1 == value2

    def ne(self, value1, value2):
        """ Determine if two values are not equal. """
        return value1 != value2

    def lt(self, value1, value2):
        """ Determine if value1 is < value2 """
        return value1 < value2

    def gt(self, value1, value2):
        """ Determine if value1 is > value2 """
        return value1 > value2

    def le(self, value1, value2):
        """ Determine if value1 is <= value2 """
        return value1 <= value2

    def ge(self, value1, value2):
        """ Determine if value1 is >= value2 """
        return value1 >= value2

    def seq(self, start, end, step=None):
        """ Return a generater sequence from start up to end. """
        return range(start, end, 1)

