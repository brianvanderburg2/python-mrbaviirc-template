""" Template Environment """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"

__all__ = ["Environment"]


import threading


from .template import Template
from .loaders import UnrestrictedLoader

from .lib import StandardLib

class Environment(object):
    """ Represent a template environment.

    This class servers as the main container for a template environment,
    storing the loaders, imports, registered hooks, etc.
    """

    def __init__(self, loader=None, importers=None):
        """ Initialize the template environment.

        Parameters
        ----------
        loader : template.Loader, optional
            Loader to use when loading files.  A value of Null will result in
            using an instance of template.UnrestrictedLoader
        importers : dict, optional
            Dictionary of name to import functions to use when a template loads
            an import.  The function takes no arguments and returns the value
            to be assigned in the template.  The result of the function is
            cached.  An initial name of "mrbaviirc.template" maps to the
            StandardLib class.
        """

        self._importers = {
            "mrbaviirc.template": StandardLib
        }
        self._imported = {}
        self._hooks = {}
        self._lock = threading.Lock()

        if loader:
            self._loader = loader
        else:
            self._loader = UnrestrictedLoader()

        if importers:
            self._importers.update(importers)

    def register_importer(self, name, importer):
        """ Register an importer.

        Register a callback to be used with the import template tag.  If an
        importer of the same name already exists, it will be replaced.

        Parameters
        ----------
        name : str
            The name of the importer used by the template.
        importer : callable
            A callable object that takes no arguments and returns a value to
            assign in the template.  This returned value will be cached and
            the importer is only called once.
        """
        self._importers[name] = importer

    def register_hook(self, name, callback):
        """ Register a hook.

        Register a hook callback to be used when a template has a hook tag.
        All hooks registered with the same name are called in the order they
        were registered, or reverse order if the reverse parameter is True.
        Hooks are passed certain elements and can render data into the current
        renderer, set variables in the state, or even include other templates
        into the renderer's output.

        Parameters
        ----------
        name : str
            The name of the hook.
        callback : callable
                A callable to register.

                The signature of the callable is as follows::

                    callback(state, params)

                state : mrbaviirc.template.state.RenderState
                    Contains the state information of the render
                params : list
                    A list of evaluated parameters passed to the hook
        """
        self._hooks.setdefault(name, []).append(callback)

    def load_file(self, filename, parent=None):
        """ Load a template from a file.

        Parameters
        ----------
        filename : str
            The filename of the template to load.  This value depends on the
            template loader used.
        parent : template.Template, default=None
            The parent template this is loading the new template. This is used
            mainly if the template is being included within the context of
            another template, so the parent template's path is used for for any
            relative paths specified in the filename.

        Returns
        -------
        template.Template:
            The loaded or cached template.

        Raises
        ------
        template.RestrictedError:
            A template loader restricted the load.
        template.ParserError:
            An error occurred during parsing.
        Exception:
            Any other exceptions such as IO/OS errors.
        """
        return self._loader.load_template(self, filename, parent)

    def load_text(self, text, filename=""):
        """ Load a template direct from text.

        Parameters
        ----------
        text : str
            The text of the template to load.
        filename : str, default=""
            The value to set as the template filename. Some loaders may use this
            for relative includes.  It is also used in error reporting.

        Returns
        -------
        template.Template:
            The loaded template. Results from loading from text are not cached.

        Raises
        ------
        template.ParserError:
            An error occurred during parsing.
        Exception:
            Another exception occurred
        """
        template = Template(self, text, filename)
        self._loader.fix_load_text(template)
        return template

    def load_import(self, name):
        """ Internal use only.  Load an import by name and cache the value.

        Parameters
        ----------
        name : str
            The name of the importer to call

        Returns
        -------
        Any
            Returns any value returned from the importer.

        Raises
        ------
        KeyError
            Raised if the named importer does not exist.
        """
        with self._lock:
            if not name in self._imported:
                if not name in self._importers:
                    raise KeyError(name)

                self._imported[name] = self._importers[name]()

            return self._imported[name]

    def call_hook(self, hook, state, params, reverse):
        """ Internal use only.  Call hooks from a template.

        This method calls a hook of a given name in forward or reverse order.
        It is not an error for the hook to not exists.  Various state paremters
        are passed to the hook functions to use as they need.

        Parameters
        ----------
        hook : str
            The name of the hook to call
        state : mrbaviirc.template.state.RenderState
            The current render state
        params : list
            A list of evaluated parameters to pass to the hook functions
        reverse : bool
            If True, the hook fuctions are called in the reverse order in which
            they were registered. Otherwise they are called in order.
        """
        callbacks = self._hooks.get(hook, None)
        if callbacks is None:
            return

        if reverse:
            callbacks = reversed(callbacks)

        for callback in callbacks:
            callback(state, params)
