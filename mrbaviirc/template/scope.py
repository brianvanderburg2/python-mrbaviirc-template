""" Provide a scope to hold variables.

Classes
-------
Scope
    The scope holdes variables as well as render-specific data.
"""

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


class Scope(object):
    """ Represent the variables and render data.

    Constants
    ---------
    SCOPE_LOCAL
        Specify to act on the current local scope.
    SCOPE_GLOBAL
        Specify to act on the global scope (the top scope's local scope).
    SCOPE_TEMPLATE
        Specify to act on the template scope (the scope pushed when the last
        template.render_nested call was issued).
    SCOPE_PRIVATE
        Specify to operate on the current private scope (the current local scope
        but none of the parent scopes).

    Attributes
    ----------
    userdata : variant
        Userdata passed to top render call.

    Methods
    -------
    push(self, template=False)
        Push a new nested scope.
    set(self, name, value, where=SCOPE_LOCAL)
        Set a value in the scope at a specific level.
    update(self, values)
        Update values in the local scope.
    unset(self, name)
        Unset a name in the local and private scope.
    get(self, variable)
        Get a variable by walking up the scope until it is found.

    Internal API Attributes
    -----------------------
    abort_fn : callable
        An abort function passed to the top render call.
        callback() : bool
            Parameters
            ----------
            None

            Returns
            -------
            bool
                True to abort, otherwise continue.
    template_scope : dict
        Reference to the current template scope.  This is used mainly by the
        return template tag to set and update the returned values.  set
        can't directly be used b/c we need to get/update the value directly
        from the template scope dict.
    """
    SCOPE_LOCAL = 0
    SCOPE_GLOBAL = 1
    SCOPE_TEMPLATE = 2
    SCOPE_PRIVATE = 3

    def __init__(self, userdata=None, abort_fn=None):
        """ Initialize our render scope.

        Parameters
        ----------
        userdata : variant, default=None
            User data to be passed to special functions and hooks.

        abort_fn : callback, default=None
            A callback to set for the abort function.
        """

        # Per-top-level-render data
        self.userdata = userdata
        self.abort_fn = abort_fn

        # Scope data
        self.parent = None
        self.local_scope = {}
        self.private_scope = {}

        # We are a new top-level scope, so set defaults
        self.global_scope = self.local_scope
        self.template_scope = None

    def push(self, template=False):
        """ Create a new nested scope.

        Parameters
        ----------
        template : bool, default=False
            If Frue, the new scope's template scope will be set to it's local
            scope.  If False, the new scope's template scope will be the same
            as the current scope's template scope.

        Returns
        -------
        template.Scope
            The new scope object.
        """
        # Create new scope with top-level-render data
        scope = Scope(self.userdata, self.abort_fn)

        # Point to use as parent and set global/template scopes accordingly
        scope.parent = self
        scope.global_scope = self.global_scope
        if template:
            scope.template_scope = scope.local_scope
        else:
            scope.template_scope = self.template_scope

        return scope

    def set(self, name, value, where=SCOPE_LOCAL):
        """ Set a value in the a scope.

        Parameters
        ----------
        name : str
            The name of the value to set
        value : variant
            The value to set
        where : enum
            One of SCOPE_LOCAL, SCOPE_GLOBAL, SCOPE_TEMPLATE or SCOPE_PRIVATE
            to specify where the template is set.  SCOPE_PRIVATE is a special
            variation of SCOPE_LOCAL in that a variable that is set in the
            private scope will only be returned by "get" when it is the current
            scope, but if it is a parent scope.

        Returns
        -------
        None
        """
        if where == Scope.SCOPE_LOCAL:
            self.local_scope[name] = value
        elif where == Scope.SCOPE_GLOBAL:
            self.global_scope[name] = value
        elif where == Scope.SCOPE_TEMPLATE:
            self.template_scope[name] = value
        elif where == Scope.SCOPE_PRIVATE:
            self.private_scope[name] = value
        else:
            # Shold never happen, but default to local
            self.local_scope[name] = value

    def update(self, values):
        """ Update values in the local scope.

        Parameters
        ----------
        values : dict
            Dictionary of name : variant values to update.

        Returns
        -------
        None
        """
        self.local_scope.update(values)

    def unset(self, name):
        """ Unset a variable from the current scope.

        Parameters
        ----------
        name : str
            Name of the variable to remove.

        Returns
        -------
        None
        """
        self.local_scope.pop(name, None)
        self.private_scope.pop(name, None)

    def clear(self):
        """ Clear the current context. """
        self.local_scope.clear()
        self.private_scope.clear()

    def get(self, var):
        """ Get a variable by walking up the scopes until it is found.

        Parameters
        ----------
        var : str
            The name of the variable to get.

        Returns
        -------
        variant
            The value of the found variable.

        Raises
        ------
        KeyErorr
            Raised if the variable was not found.
        """

        # Find the scope dict it is in
        cur = self
        found = None

        while cur is not None:
            # Try private scope first
            if cur is self and var in cur.private_scope:
                found = cur.private_scope
                break

            if var in cur.local_scope:
                found = cur.local_scope
                break

            # Walk up the scopes
            cur = cur.parent

        if found is None:
            raise KeyError(var)

        return found[var]
