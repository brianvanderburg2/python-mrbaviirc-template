""" Path library for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016-2019"
__license__     = "Apache License 2.0"


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


FACTORY = _PathLib
