""" Template Environment """
# pylint: disable=too-many-arguments

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

    def __init__(self, loader=None, importers=None, allow_code=False):
        """ Initialize the template environment.

        Args:
            loader (template.Loader,optional):
                Template loader to use when loading files. Defaults to None.
            importers (dict,optional):
                A dictionary of name: callback importers.  Defaults to None.
                When a template imports a registered library, the return value
                of the callback is returned to the template.  The result is
                cached so the callback is only called once.
            allow_code (bool,optional):
                Global flag to enable or disable code blocks in the template.
                Defaults to False. If this flag is false, code blocks will be
                disable even if they are enabled locally for a given template.
        """

        self.importers = {
            "mrbaviirc.template": StandardLib
        }
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

        Args:
            name (str): The name of the importer used by the template.
            importer (callable): A callable object that takes no arguments and
                returns a value to assign in the template.  This returned value
                will be cached and the importer is only called once.
        """
        self.importers[name] = importer

    def register_hook(self, name, callback):
        """ Register a hook.

        Register a hook callback to be used when a template has a hook tag.
        All hooks registered with the same name are called in the order they
        were registered, or reverse order if the reverse parameter is True.
        Hooks are passed certain elements and can render data into the current
        renderer, set variables in the scope, or even include other templates
        into the renderer's output.

        Args:
            name (str): The name of the hook.
            callback (callable):  A callable to register.
                The signature of the callable is as follows::

                    callback(env, template, line, renderer, scope, params)

                env (template.Environment):
                    The environment the template calling the hook is part of
                template (template.Template):
                    The template object the hook is called from
                line (int):
                    The line number the hook tag is called from
                renderer (template.Renderer):
                    The renderer object being used
                scope (template.Scope):
                    The scope containing variables, userdata, etc
                params (list):
                    A list of evaluated parameters passed to the hook
        """
        self.hooks.setdefault(name, []).append(callback)

    def allow_code(self, enabled=True):
        """ Enable use of the code tag in templates.

        Args:
            enabled (bool,optional): Set the global code enabled flag. Default
                value is True.
        """
        self.code_enabled = enabled

    def load_file(self, filename, parent=None):
        """ Load a template from a file.

        Args:
            filename (str): The filename of the template to load.  This value
                depends on the template loader used.
            parent (template.Template): The parent template this is loading
                the new template. Default value is None.  This is used mainly
                if the template is being included within the context of another
                template, so the parent template's path is used for for any
                relative paths specified in the filename.

        Returns:
            template.Template: The loaded or cached template.

        Raises:
            template.RestrictedError: A template loader restricted the load.
            template.ParserError: An error occurred during parsing.
            Exception: Any other exceptions such as IO/OS errors.
        """
        return self.loader.load_template(self, filename, parent)

    def load_text(self, text, filename="", allow_code=False):
        """ Load a template direct from text.

        Args:
            text (str): The text of the template to load.
            filename (str,optional): The value to set as the template filename.
                Default is an empty string. Some loaders may use this for
                relative includes.  It is also used in error reporting.
            allow_code (bool,optional) The value to set for the template's
                local allow code flag. Default is False

        Returns:
            template.Template: The loaded template. Results from loading from
                text are never cached.

        Raises:
            template.ParserError: An error occurred during parsing.
            Exception: Another exception occurred
        """
        template = Template(self, text, filename, allow_code)
        self.loader.fix_load_text(template)
        return template

    def load_import(self, name):
        with self.lock:
            if not name in self.imported:
                if not name in self.importers:
                    raise KeyError(name)

                self.imported[name] = self.importers[name]()

            return self.imported[name]

    def call_hook(self, hook, template, line, renderer, scope, params, reverse):
        callbacks = self.hooks.get(hook, None)
        if callbacks is None:
            return

        if reverse:
            callbacks = reversed(callbacks)

        for callback in callbacks:
            callback(self, template, line, renderer, scope, params)
