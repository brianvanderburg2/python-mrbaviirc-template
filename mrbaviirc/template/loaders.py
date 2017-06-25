""" Provide a loader for loading templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

__all__ = ["Loader", "UnrestrictedLoader", "SearchPathLoader"]

import os
import posixpath

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


class UnrestrictedLoader(Loader):
    """ A loader that loads any template specified. """

    def __init__(self):
        """ Initialized the loader. """
        Loader.__init__(self)

        self._cache = {}

    def load_template(self, env, filename, parent=None):
        """ Load a template. """

        # Determine filename from parent if needed
        if parent:
            filename = os.path.join(
                os.path.dirname(parent._filename),
                filename.replace("/", os.sep)
            )

        filename = os.path.realpath(filename)

        # Available from cache?
        if filename in self._cache:
            return self._cache[filename]

        # Load and return
        with open(filename, "rU") as handle:
            text = handle.read()

        self._cache[filename] = Template(env, text, filename)
        return self._cache[filename]


class SearchPathLoader(Loader):
    """ A loader that loads the template from the file system. """

    def __init__(self, path):
        """ Initialze the loader. """

        Loader.__init__(self)

        if not isinstance(path, (tuple, list)):
            path = [path]

        self._path = tuple(os.path.realpath(i) for i in path)
        self._cache = {}
        self._find_cache = {}

    def load_template(self, env, filename, parent=None):
        """ Load a template. """

        # Determine filename from parent
        filename = os.path.normpath(posixpath.join(
            "/", # to make sure it's always absolute
            posixpath.dirname(parent._filename) if parent else "/",
            filename
        ))

        # Available from cache?
        if filename in self._cache:
            return self._cache[filename]

        # Find the real file and load it
        realname = self._find_template(filename)
        with open(realname, "rU") as handle:
            text = handle.read()

        self._cache[filename] = Template(env, text, filename)
        return self._cache[filename]

    def _find_template(self, filename):
        """ Find a template along search path. """

        filename = filename.lstrip("/").replace("/", os.sep)

        if not self._path:
            raise RestrictedError(
                "Attempt to load template from empty search path: {0}".format(filename)
            )

        if not filename in self._find_cache:
            for path in self._path:
                new_filename = os.path.realpath(os.path.join(path, filename))
                if os.path.isfile(new_filename):
                    self._find_cache[filename] = new_filename
                    break
            else:
                raise RestrictedError(
                    "Template not found along search path: {0}".format(filename)
                )

        return self._find_cache[filename]

