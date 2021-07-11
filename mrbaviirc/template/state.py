""" Classes that maintain state for the template engine. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"


from .renderers import StringRenderer


class RenderState:
    """ Represent the state of information during a render cycle.

    The primary function of this class is the container for the template's
    variables, but it also serves to contain other data such as userdata, abort
    function, etc.

    Attributes
    ----------
    env
        The environment object associated with the template render
    template
        The template object currently being rendered
    line
        The line number of the template element
    user_data
        The user data passed to render
    renderer
        The current renderer
    """

    # LOCAl, PRIVATE, INTERNAL, and RETURN are per nested_render
    LOCAL_VAR = 0
    GLOBAL_VAR = 1
    PRIVATE_VAR = 2
    INTERNAL_VAR = 3
    RETURN_VAR = 4
    APP_VAR = 5

    def __init__(self):
        """ Initialize the render context. """
        # May be accesed outside the template API in hook functions/etc as read only
        self.env = None
        self.template = None
        self.line = 0
        self.renderer = None
        self.sections = {}
        self.user_data = None

        # Should only be accessed within the API or this class
        self.abort_fn = None
        self._vars = [{}, {}, {}, {}, {}, {}] # Indexed via the type of variable
        self._template_stack = []
        self._renderer_stack = []

    def set_var(self, name, value, where=LOCAL_VAR):
        """ Set a variable.

        Parameters
        ----------
        name : str
            The name of a variable to set
        value : Any
            The value of a variable to set
        where : LOCAL_VAR or GLOBAL_VAR or PRIVATE_VAR or RETURN_VAR
            Where to set the variable
        """

        self._vars[where][name] = value

    def update_vars(self, values, where=LOCAL_VAR):
        """ Update variables.

        Parameters
        ----------
        values : dict
            A dictionary of values to update
        where : LOCAL_VAR or GLOBAL_VAR or PRIVATE_VAR or RETURN_VAR
            Where to update the variables
        """
        self._vars[where].update(values)

    def get_var(self, name, where=LOCAL_VAR):
        """ Get a variable.

        Parameters
        ----------
        name : str
            The name of the variable to get
        where : LOCAL_VAR or GLOBAL_VAR or PRIVATE_VAR or RETURN_VAR
            Where to look for the variable

        Returns
        -------
        Any
            The current value of the variable

        Raises
        ------
        KeyError
            If the variable is not found, KeyError will be raised
        """

        return self._vars[where][name]

    def unset_var(self, name, where=LOCAL_VAR):
        """ Remove a variable.

        Parameters
        ----------
        name : str
            Name of the variable to remote
        where : LOCAL_VAR or GLOBAL_VAR or PRIVATE_VAR or RETURN_VAR
            Where to remove the variable
        """

        self._vars[where].pop(name, None)

    def clear_vars(self, where=LOCAL_VAR):
        """ Clear all variables in a compartment.

        Parameters
        ----------
        where : LOCAL_VAR or GLOBAL_VAR or PRIVATE_VAR or RETURN_VAR
            Where to remove the variable
        """
        self._vars[where].clear()

    def enter_template(self, template):
        """ Starting a template render, remember the current state needed.

        Parameters
        ----------
        template :
            The template the render cycle is about to process
        """

        self._template_stack.append((
            self.template,
            self._vars[self.LOCAL_VAR],
            self._vars[self.PRIVATE_VAR],
            self._vars[self.INTERNAL_VAR],
            self._vars[self.RETURN_VAR]
        ))

        self._vars[self.LOCAL_VAR] = self._vars[self.LOCAL_VAR].copy()
        # GLOBAL_VAR no change
        self._vars[self.PRIVATE_VAR] = {}
        self._vars[self.INTERNAL_VAR] = {}
        self._vars[self.RETURN_VAR] = {}
        # APP_VAR no change

        self.template = template
        self.line = 0

    def leave_template(self):
        """ Leaving a template render, restore the state needed.

        Returns
        -------
        dict
            The return dictionary of values to be set in the calling template.
        """

        result = self._vars[self.RETURN_VAR]

        (
            self.template,
            self._vars[self.LOCAL_VAR],
            self._vars[self.PRIVATE_VAR],
            self._vars[self.INTERNAL_VAR],
            self._vars[self.RETURN_VAR]
        ) = self._template_stack.pop()

        return result

    def push_renderer(self, renderer=None):
        """ Change the current renderer.

        Parameters
        ----------
        renderer :
            The render to use. This defaults to None, which will result in using
            a new instance of a StringRenderer.

        Returns
        -------
        Renderer
            Returns the new renderer
        """
        if renderer is None:
            renderer = StringRenderer()

        self._renderer_stack.append(self.renderer)
        self.renderer = renderer
        return renderer

    def pop_renderer(self):
        """ Restore the previous renderer. """
        self.renderer = self._renderer_stack.pop()

    def append_section(self, name, contents):
        """ Append content to a section.

        Parameters
        ----------
        name : str
            The name of the section to append to

        contents : str
            The contents to append to the section
        """
        section = self.sections.setdefault(name, [])
        section.append(contents)

    def get_section(self, name):
        """ Get the contents of a section.

        Parameters
        ----------
        name : str
            The name of the section to retrieve

        Returns
        -------
        str
            The contents of the section
        """
        return "".join(self.sections.get(name, []))

    def get_result(self):
        """ Get the render result. """

        result = RenderResult()

        result.user_data = self.user_data
        result.renderer = self.renderer
        result.vars = self._vars[self.APP_VAR]

        # Sections
        result.sections = {
            section : "".join(contents)
            for (section, contents) in self.sections.items()
        }

        return result

class RenderResult:
    """ Represent information about the result of a render. """

    def __init__(self):
        """ Initialize the results. """

        self.user_data = None
        self.renderer = None
        self.vars = {}
        self.sections = {}
