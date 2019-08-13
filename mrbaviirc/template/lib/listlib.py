""" List library for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016-2019"
__license__     = "Apache License 2.0"


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


FACTORY = _ListLib
