""" Provide a loader for loading templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

__all__ = ["Loader", "FileSystemLoader"]

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


class FileSystemLoader(Loader):
    """ A loader that loads the template from the file system. """

    def __init__(self, root=None):
        """ Initialze the loader. """
        if root:
            if not isinstance(root, (tuple, list)):
                root = [root]
            self._root = tuple([os.path.join(os.path.realpath(i), '') for i in root])
        else:
            self._root = None

        self._cache = {}
        self._find_cache = {}

    def load_template(self, env, filename, parent=None):
        """ Load a template. """

        if filename[0:2] == '@/':
            # Absolute relname to roots
            relname = posixpath.normpath(filename[1:]).lstrip('/')
            filename = self._find_template(relname)

            if filename in self._cache:
                return self._cache[filename]

        elif filename[0:1] == '@':
            # Relative relname to roots relative to parent relname
            relname = posixpath.normpath(posixpath.join(
                '/',
                posixpath.dirname(parent._relname) if parent else "",
                filename[1:]
            )).lstrip('/')
            filename = self._find_template(relname)

            if filename in self._cache:
                return self._cache[filename]

        else:
            # Relative to current file or PWD
            # Will find relname only if using roots
            if parent:
                filename = os.path.join(
                    os.path.dirname(parent._filename),
                    *(filename.split('/'))
                )

            filename = os.path.realpath(filename)
            if filename in self._cache:
                return self._cache[filename]

            # Check roots if need
            if self._root:
                for root in self._root:
                    if os.path.commonprefix([filename, root]) == root and os.path.isfile(filename):
                        relname = os.path.relpath(filename, root).replace(os.sep, '/')
                        relname = posixpath.normpath(relname).lstrip('/')
                        break
                else:
                    raise RestrictedError(
                        "Attempt to load template out of root: {0}".format(filename)
                    )

            else:
                relname = ""

        # At this point we have the filename and relname to use
        with open(filename, "rU") as handle:
            text = handle.read()

        self._cache[filename] = Template(env, text, filename, relname)
        return self._cache[filename]

    def _find_template(self, filename):
        """ Find a template along root paths. """

        filename = filename.replace("/", os.sep)

        if not self._root:
            raise RestrictedError(
                "Attempt to load template from empty search path: {0}".format(filename)
            )

        if not filename in self._find_cache:
            for root in self._root:
                new_filename = os.path.realpath(os.path.join(root, filename))
                if os.path.isfile(new_filename):
                    self._find_cache[filename] = new_filename
                    break
            else:
                raise RestrictedError(
                    "Template not found along search path: {0}".format(filename)
                )

        return self._find_cache[filename]

