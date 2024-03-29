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
from .state import RenderState


class Template:
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

    render(self, renderer, context=None, user_data=None, abort_fn=None)
        The top level call to a render.
    nested_render(self, state, context)
        An including render passing along the state information.

    Internal API Attributes
    -----------------------
    private : dict
        A private dictionary for data to be added by the loaders.
    lock : threading.Lock
        A lock for handling multithreaded loads from the loader

    Internal API Methods
    --------------------
    __init__(self, env, text, filename)
        Create the template
    """

    def __init__(self, env, text, filename):
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
        """

        # Initialize
        self._env = weakref.ref(env)
        self.filename = filename

        self.private = {}
        self.lock = threading.Lock()

        # Parse the template
        parser = TemplateParser(self, text)
        self.nodes = parser.parse()

    @property
    def env(self):
        """ Get the environment object or None. """
        return self._env()

    def render(self, renderer, context=None, user_data=None, abort_fn=None):
        """ Render the template.

        Parameters
        ----------
        renderer : template.Renderer
            The renderer the output should be rendered to.
        context : dict, default=None
            Initial values to set into the local variables
        user_data : variant, default=None
            Userdata to pass to the render state
        abort_fn : callback, default=None
            The abort callback function to pass to the render state

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

        # Create the render state
        state = RenderState()
        state.env = self.env
        state.user_data = user_data
        state.abort_fn = abort_fn
        state.renderer = renderer

        self.nested_render(state, context)

        return state.get_result()


    def nested_render(self, state, context):
        """ Render the template from within another template/state.

        Paramters
        ---------
        state : mrbaviirc.template.state.RenderState
            The current state of the render
        context : dict
            Variable to set into the local variables of the render.

        Raises
        ------
        template.Error
            Any error raised during rendering
        Exception
            Any other error
        """
        retval = {}
        try:
            state.enter_template(self)
            if context is not None:
                state.update_vars(context)

            # set certain variables
            state.set_var("__filename__", self.filename) # Note this is local

            self.nodes.render(state)
        finally:
            retval = state.leave_template()

        return retval
