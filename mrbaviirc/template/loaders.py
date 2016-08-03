""" Provide a loader for loading templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

__all__ = ["Loader", "FileSystemLoader"]

import os

from .template import Template

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

    def __init__(self):
        """ Initialze the loader. """
        self._cache = {}

    def load_template(self, env, filename, parent=None):
        """ Load a template. """

        if parent:
            filename = os.path.join(
                os.path.dirname(parent),
                *(filename.split("/"))
            )

        filename = os.path.abspath(os.path.normpath(filename))

        if not filename in self._cache:
            with open(filename, "rU") as handle:
                text = handle.read()

            self._cache[filename] = Template(env, text, filename)

        return self._cache[filename]

