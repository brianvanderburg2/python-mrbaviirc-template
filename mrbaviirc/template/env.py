""" Template Environment.

Classes
-------
Environment
    Represent the template environment.


"""
# pylint: disable=too-many-arguments

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"

__all__ = ["Environment"]


import threading


from .template import Template
from .loaders import UnrestrictedLoader

from .lib import StdLib

class Environment(object):
    """ Represent a template environment.

    This class servers as the main container for a template environment,
    storing the loaders, imports, registered hooks, etc.

    Methods
    -------
    __init__(self, loader=None, imports=None, allow_code=False)
        Create the template environment.

    register_importer(self, name, importer)
        Register an importable library for templates.

    register_hook(self, name, callback)
        Register a hook for templates.

    allow_code(self, enabled=True)
        Enable or disable code tags in templates.

    load_file(self, filename, parent=None)
        Load a template using the loader.

    load_text(self, text, filename="", allow_code=False)
        Load a template from text.

    Internal API Methods
    --------------------

    load_import(self, name)
        Load an import library.
    call_hook(self, hoook, template, line, renderer, scope, params, reverse)
        Call registered hooks.

    Internal API Attributes
    -----------------------
    code_enabled
        Flag indicating whether code tags are enabled or disabled globally.
        If this flag is True, then a templates local flag determines if
        the code tag can be used in that template.  If this flag is False
        then code tags cannot be used even if the template's local flag is
        True.
    """

    def __init__(self, loader=None, importers=None, allow_code=False):
        """ Initialize the template environment.

        Parameters
        ----------
        loader : template.Loader, default=None
            Template loader to use when loading files.
        importers : dict, default=None
            A dictionary of name: callback importers.  When a template imports
            a registered library, the return value of the callback is returned
            to the template.  The result is cached so the callback is only
            called once.
        allow_code : bool, default=False
            Global flag to enable or disable code blocks in the template. If
            this flag is false, code blocks will be disable even if they are
            enabled locally for a given template.
        """

        self.importers = {"mrbaviirc.template.stdlib": StdLib}
        self.imported = {}
        self.hooks = {}
        self.code_enabled = allow_code
        self.lock = threading.Lock()

        if loader:
            self.loader = loader
        else:
            self.loader = UnrestrictedLoader()

        if importers:
            self.importers.update(importers)

    def register_importer(self, name, importer):
        """ Register an importer.

        Register a callback to be used with the import template tag.

        Paramters
        ---------
        name : str
            The name of the importer.
        importer : callable
            A callable that takes no arguments and returns the value to
            assign to the variable in the template.

        Returns
        -------
        None
        """
        self.importers[name] = importer

    def register_hook(self, name, callback):
        """ Register a hook.

        Register a hook callback to be used when a template has a hook tag.

        Parameters
        ----------
        name : str
            The name of the hook.
        callback : callable
            A callable to register.  The signature of the callable:

                callback(env, template, line, renderer, scope, params)
                env : template.Environment
                    The environment the template calling the hook is part of
                template : template.Template
                    The template object the hook is called from
                line : int
                    The line number the hook tag is called from
                renderer : template.Renderer
                    The renderer object being used
                scope : template.Scope
                    The scope containing variables, userdata, etc
                params : list
                    A list of evaluated parameters passed to the hook

        Returns
        -------
        None
        """
        self.hooks.setdefault(name, []).append(callback)

    def allow_code(self, enabled=True):
        """ Enable use of the code tag in templates.

        Parameters
        ----------
        enabled : bool, defafult=True
            Set the global code enabled flag.
        """
        self.code_enabled = enabled

    def load_file(self, filename, parent=None):
        """ Load a template from a file.

        Parameters
        ----------
        filename : str
            The filename with respect to the loader to be loaded.
        parent : template.Template, default=None
            The template object to use as the including template.

        Returns
        -------
        template.Template
            The loaded or cached template.

        Raises
        ------
        template.RestrictedError
            A template loader restricted the load.
        template.ParserError
            An error occured during parsing.
        Exception
            Standard OS exceptions.
        """
        return self.loader.load_template(self, filename, parent)

    def load_text(self, text, filename="", allow_code=False):
        """ Load a template direct from text.

        Parameters
        ----------
        text : str
            The text of the template to load.
        filename : str, default=""
            The value to set as the templates filename.  Some loaders may use
            this for relative includes.  It is also used in error reporting.
        allow_code : bool, default=False
            The value to set for the template's local allow code flag.

        Returns
        -------
        template.Template
            The loaded or cached template.

        Raises
        ------
        template.RestrictedError
            A template loader restricted the load.
        template.ParserError
            An error occured during parsing.
        Exception
            Standard OS exceptions.
        """
        template = Template(self, text, filename, allow_code)
        self.loader.fix_load_text(template)
        return template

    def load_import(self, name):
        """ Load a library from an importer.

        Paramters
        ---------
        name : str
            The name of the import to load.

        Returns
        -------
        Variant
            The return value is whather the importer callback returns.

        Raises
        ------
        KeyError
            Raised if the specific importer is not registered.
        """

        with self.lock:
            if not name in self.imported:
                if not name in self.importers:
                    raise KeyError(name)

                self.imported[name] = self.importers[name]()

            return self.imported[name]

    def call_hook(self, hook, template, line, renderer, scope, params, reverse):
        """ Call a hook if it exist, otherwise just return.

        All hooks registered with the same name are called in the order they
        were registered, or reverse order if the reverse parameter is True.
        Hooks are passed certain elements and can render data into the current
        renderer, set variables in the scope, or even include other templates
        into the renderer's output.

        Paramters
        ---------
        hook : str
            The name of the hook to call.
        template : template.Template
            The template the hook is being called from.
        line : int
            The line number the hook is called from.
        renderer : template.Renderer
            The renderer object for the template render.
        scope : template.Scope
            The current scope object for the template render.
        params : dict
            Dictionary of name: value parameters passed to the hook.
        reverse : bool
            If True, calls the registered hooks of the given name in reverse
            order to how they were registered. If False, call them in the same
            order they were registered.
        """

        callbacks = self.hooks.get(hook, None)
        if callbacks is None:
            return

        if reverse:
            callbacks = reversed(callbacks)

        for callback in callbacks:
            callback(self, template, line, renderer, scope, params)
