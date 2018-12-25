""" Provide a loader for loading templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

__all__ = ["Loader", "UnrestrictedLoader", "SearchPathLoader", "MemoryLoader",
           "PrefixLoader", "PrefixSubLoader", "PrefixPathLoader", "PrefixMemoryLoader"]

import os
import posixpath
import threading

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

    def load_template(self, env, filename, parent=None):
        raise NotImplementedError


class UnrestrictedLoader(Loader):
    """ A loader that loads any template specified. """

    def __init__(self):
        """ Initialized the loader. """
        Loader.__init__(self)

        self._cache = {}
        self._lock = threading.Lock()

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
        with self._lock:
            if filename in self._cache:
                return self._cache[filename]

            # Load and return
            with open(filename, "rU") as handle:
                text = handle.read()

            self._cache[filename] = Template(env, text, filename, allow_code=True)
            return self._cache[filename]


class PrefixLoader(Loader):
    """ A loader that allows registering specific prefixes to map to certain
        loaders. """

    def __init__(self):
        """ Initialize the loader. """
        Loader.__init__(self)

        self._prefixes = []
        self._cache = {}
        self._lock = threading.Lock()

    def add_prefix(self, prefix, loader):
        """ Add a prefix to the loader. """
        prefix = tuple(i for i in prefix.split("/") if len(i.strip()))
        self._prefixes.append((prefix, loader))

    def load_template(self, env, filename, parent=None):
        """ Load a template. """

        # Private data stored in template:
        # path - A tuple consisting of the path of the template
        # index - The index in the list of prefixes the template was found
        # normalized = (path, index, cachename) of a filename if already
        #   loaded from the same template

        # First normalize the name based on the parent and store the normalized
        # value in the parent's cache
        if parent:
            parent._lock.acquire()

        try:
            if parent and filename in parent._private["normalized"]:
                # We've already included the same filename from the same parent
                # and cached the normalized result, no need to normalize again
                (path, index_start, cache_name) = parent._private["normalized"][filename]
            elif filename == ":next:":
                # Load the same path as the parent starting at the next prefix entry
                if parent is None:
                    raise RestrictedError(":next: can only be ncluded from an existing template.")

                path = parent._private["path"]
                index_start = parent._private["index"] + 1
                cache_name = ":@@{0}@@:{1}".format(index_start, "/".join(path))
            else:
                # Loading a template directly by path
                path = self._normalize(filename, parent._private["path"] if parent else None)
                index_start = 0
                cache_name = "/".join(path)

            # Cache the normalization results if loading from an include
            if parent:
                normalized = parent._private["normalized"]
                normalized[filename] = (path, index_start, cache_name)
        finally:
            if parent:
                parent._lock.release()

        with self._lock:
            # Check if already loaded
            if cache_name in self._cache:
                return self._cache[cache_name]

            # Find all matching prefixes and attempt to load the template
            template = None
            index = -1
            for index, (prefix, loader) in enumerate(
                self._prefixes[index_start:],
                index_start
            ):
                # Make sure first parts are common
                if len(path) < len(prefix):
                    # This will allow a situation where the subpath may be empty
                    # is if path to load matches the prefix exactly. This is
                    # intentional in case t here is an actualy use for it.
                    # Subloader should check for an empty load path
                    continue

                if path[:len(prefix)] != prefix:
                    continue

                subpath = path[len(prefix):]
                template = loader.load_template(env, subpath, path)
                if template:
                    break

            if template:
                template._private["path"] = path
                template._private["index"] = index
                template._private["normalized"] = {}
                self._cache[cache_name] = template
                return template
            elif parent:
                raise RestrictedError(
                    "Template not found along prefix paths: {0}, Included from: {1}".format(
                        filename, # We use filename so user can tell which include cause the problem
                        "/".join(parent._private["path"])
                    )
                )
            else:
                raise RestrictedError(
                    "Template not found along prefix paths: {0}".format(filename)
                )

    def _normalize(self, filename, path):
        """ Normalize the path and return the path tuple """

        # Convert filename to tuple first
        filepath = [i for i in filename.split("/") if len(i.strip())]
        absolute = filename[0:1] == "/"

        if path and not absolute:
             # Remove last component so path is the parent directory
            newpath = list(path[:-1])
        else:
            newpath = []

        # Remove "." and ".." from file path
        for part in filepath:
            if part == ".":
                continue
            elif part == "..":
                if len(newpath) == 0:
                    if path:
                        raise RestrictedError("Relative include error: {0}, From: {1}".format(
                            filename,
                            "/".join(path)
                        ))
                    else:
                        raise RestrictedError("Relative load error: {0}".format(
                            filename
                        ))
                else:
                    newpath.pop()
            else:
                newpath.append(part)

        return tuple(newpath)


class PrefixSubLoader(object):
    """ A subloader added to a PrefixLoader. """

    def __init__(self):
        """ Initialize the loader. """
        pass

    def load_template(self, env, subpath, fullpath):
        """ Load the template specified by the subpath. """
        raise NotImplementedError


class PrefixPathLoader(PrefixSubLoader):
    """ Load from a path. """

    def __init__(self, path, allow_code=False):
        """ Initialize the loader with a given path. """
        PrefixSubLoader.__init__(self)
        self._path = os.path.realpath(path)
        self._allow_code = allow_code

    def load_template(self, env, subpath, fullpath):
        """ Load a given template. """

        if len(subpath) == 0:
            return None

        filename = os.path.join(
            self._path,
            "/".join(subpath)
        )

        if os.path.isfile(filename):
            with open(filename, "rU") as handle:
                text = handle.read()

            return Template(env, text, filename, self._allow_code)

        return None


class PrefixMemoryLoader(PrefixSubLoader):
    """ Load from an in-memory template. """

    def __init__(self):
        """ Initialize the loader. """
        PrefixSubLoader.__init__(self, allow_code=False)
        self._memory = {}
        self._allow_code = allow_code

    def add_template(self, path, contents):
        """ Add a memory template. """
        path = tuple(i for i in path.split("/") if len(i.strip()))
        self._memory[path] = contents

    def load_template(self, env, subpath, fullpath):
        """ Load a given memory template. """

        if subpath in self._memory:
            return Template(
                env,
                self._memory[subpath],
                ":memory:{0}".format("/".join(fullpath)),
                self._allow_code
            )

        return None


class SearchPathLoader(PrefixLoader):
    """ This loader implements the originaly SearchPathLoader """

    def __init__(self, path):
        """ Initialize the loader. """
        PrefixLoader.__init__(self)

        if not isinstance(path, (tuple, list)):
            path = [path]

        for part in path:
            self.add_prefix("", PrefixPathLoader(part, allow_code=True))


class MemoryLoader(PrefixLoader):
    """ Load from memory. """

    def __init__(self):
        """ Initialize the loader. """
        Loader.__init__(self);
        self._memory = PrefixMemoryLoader(allow_code=True)
        self.add_prefix("", self._memory)

    def add_template(self, name, contents):
        """ Add an entry to the memory. """
        self._memory.add_template(name, contents)

