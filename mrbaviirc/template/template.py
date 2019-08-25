""" Represent a single template for the template engine.

Classes
-------
Template
    A loaded template object.
"""

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


import threading
import weakref

from .parser import TemplateParser
from .scope import Scope


class Template(object):
    """ Represent a loaded template.

    Attributes
    ----------
    env : template.Environment
        The environment the template is loaded from
    filename : str
        The filename the template was loaded from.  This may be empty
        or an unknown value depending on the loader used.  It is used in error
        reporting and in some loaders for relative includes.

    Methods
    -------

    render(self, renderer, context=None, userdata=None, abort_fn=None)
        The top level call to a render.
    nested_render(self, renderer, scope, context)
        An including render passing along the previous scope.

    Internal API Attributes
    -----------------------
    code_enabled : bool
        The local code enabled flag indicating whether to allow code tags in
        the template.  If this is True, then code is enabled if the environment
        code enabled flag is also True. If this is False, code is disabled.
    private : dict
        A private dictionary for data to be added by the loaders.
    lock : threading.Lock
        A lock for handling multithreaded loads from the loader

    Internal API Methods
    --------------------
    __init__(self, env, text, filename, allow_code=False)
        Create the template
    """

    def __init__(self, env, text, filename, allow_code=False):
        """ Initialize a template with context variables.

        Parameters
        ----------
        env : template.Environment
            The environment the template is associated with
        text : str
            The text contents of the template
        filename : str
            The value to store as the template filename.  This is used for
            error reporting and by some loaders for relative includes.
        allow_code : bool, default=False
            The local code enabled flag for the template.
        """

        # Initialize
        self._env = weakref.ref(env)
        self.filename = filename
        self.code_enabled = allow_code

        self.private = {}
        self.lock = threading.Lock()

        # Parse the template
        parser = TemplateParser(self, text)
        self.nodes = parser.parse()

    @property
    def env(self):
        return self._env()

    def render(self, renderer, context=None, userdata=None, abort_fn=None):
        """ Render the template.

        Parameters
        ----------
        renderer : template.Renderer
            The renderer the output should be rendered to.
        context : dict, default=None
            Initial values to set into the local scope of the top render scope
        userdata : variant, default=None
            Userdata to pass to the scope
        abort_fn : callback, default=None
            The abort callback function to pass to the scope.

        Returns
        -------
        None

        Raises
        ------
        template.Error
            Any error raised during rendering
        Exception
            Any other error
        """

        # Create the top (global) scope for this render
        scope = Scope(self.env, userdata=userdata, abort_fn=abort_fn)
        if context is not None:
            scope.update(context)

        return self.nested_render(renderer, scope, None)

    def nested_render(self, renderer, scope, context):
        """ Render the template from within another template/scope.

        Paramters
        ---------
        renderer : template.Renderer
            The renderer the output should be rendered to.
        scope : template.Scope
            The scope to pass along to the render.
        context : dict
            Variable to set into the template scope of the render.

        Raises
        ------
        template.Error
            Any error raised during rendering
        Exception
            Any other error
        """
        new_scope = scope.push(self)

        if context is not None:
            new_scope.update(context)

        # set certain variables
        new_scope.template_scope["__filename__"] = self.filename

        self.nodes.render(renderer, new_scope)

        # Return any template return values:
        retval = new_scope.template_scope.get(":return:", {})
        return retval
