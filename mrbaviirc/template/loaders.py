""" Provide a loader for loading templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

__all__ = ["Loader", "FileSystemLoader"]

import os

from .template import Template
from .errors import *

try:
    from codecs import open
except ImportError:
    pass


class Loader(object):
    """ A loader loads and caches templates. """

    def __init__(self):
        """ Initialize the loader. """
        pass

    def load_template(filename, parent=None):
        raise NotImplementedError


class FileSystemLoader(Loader):
    """ A loader that loads the template from the file system. """

    def __init__(self, root=None):
        """ Initialze the loader. """
        self._root = os.path.join(os.path.realpath(root), '') if root else None
        self._cache = {}

    def load_template(self, env, filename, parent=None):
        """ Load a template. """

        if parent:
            filename = os.path.join(
                os.path.dirname(parent),
                *(filename.split("/"))
            )

        filename = os.path.realpath(filename)

        if not filename in self._cache:
            if self._root and not self._check(filename):
                raise RestrictedError(
                    "Attempt to load template out of root: {0}".format(filename)
                )

            with open(filename, "rU") as handle:
                text = handle.read()

            self._cache[filename] = Template(env, text, filename)

        return self._cache[filename]

    def _check(self, filename):
        """ Check the filename is under the root. """
        return os.path.commonprefix([self._root, filename]) == self._root

