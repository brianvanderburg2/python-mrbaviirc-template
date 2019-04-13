""" Provide a scope to hold variables. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


class Scope(object):
    """ Represent the different variable levels at the current scope. """
    SCOPE_LOCAL = 0
    SCOPE_GLOBAL = 1
    SCOPE_TEMPLATE = 2
    SCOPE_PRIVATE = 3

    def __init__(self, userdata=None, abort_fn=None):
        """ Initialize our render scope. """

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
        """ Create a new nested scope. """
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
        """ Set a value in the a scope. """
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
        """ Update values in the context. """
        self.local_scope.update(values)

    def unset(self, name):
        """ Unset a variable from the current scope. """
        self.local_scope.pop(name, None)
        self.private_scope.pop(name, None)

    def clear(self):
        """ Clear the current context. """
        self.local_scope.clear()
        self.private_scope.clear()

    def get(self, var):
        """ Get a variable. """

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
