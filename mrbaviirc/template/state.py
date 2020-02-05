""" Classes that maintain state for the template engine. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright (C) 2019 Brian Allen Vanderburg II"
__license__ = "Apache License 2.0"


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
        self.user_data = None

        # Should only be accessed within the API or this class
        self.abort_fn = None
        self._vars = [{}, {}, {}, {}, {}, None] # Indexed via the type of variable
        self._vars[self.APP_VAR] = self._vars[self.RETURN_VAR] # APP always refs top RETURN
        self._template_stack = []

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
        # Private and return are new dictionaries
        self._vars[self.LOCAL_VAR] = self._vars[self.LOCAL_VAR].copy()
        # GLOBAL_VAR no change
        self._vars[self.PRIVATE_VAR] = {}
        self._vars[self.INTERNAL_VAR] = {}
        self._vars[self.RETURN_VAR] = {}
        # APP_VAR continues to reference original RETURN_VAR dict
        self.template = template
        self.line = 0

    def leave_template(self):
        """ Leaving a template render, restore the state needed. """

        (
            self.template,
            self._vars[self.LOCAL_VAR],
            self._vars[self.PRIVATE_VAR],
            self._vars[self.INTERNAL_VAR],
            self._vars[self.RETURN_VAR]
        ) = self._template_stack.pop()

    def get_return(self):
        """ Get the return results.

        Returns
        -------
        dict
            This returns the return dictionary. This is only a reference
            to the internal dictionary so the returned value should not be
            used or manipulated until after leave_template has been called.
        """
        return self._vars[self.RETURN_VAR]
