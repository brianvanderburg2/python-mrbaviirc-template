""" Provide a scope to hold variables. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


class Scope(object):
    """ Represent the different variable levels at the current scope. """
    SCOPE_LOCAL = 0
    SCOPE_GLOBAL = 1
    SCOPE_TEMPLATE = 2
    SCOPE_PRIVATE = 3

    def __init__(self, parent=None, template=False):
        """ Initialize the current scope. """

        self._parent = parent
        self._local = {}

        # Private variables can only be accessed from the scope that set them
        self._private = {}

        # Set global and template
        if parent:
            self._global = parent._global

            if template:
                # We are starting a template scope
                self._template = self._local
            else:
                self._template = parent._template
        else:
            self._global = self._local
            self._template = None

    def push(self, template=False):
        """ Create new scope and return it. """
        return Scope(self, template)

    def set(self, name, value, where=SCOPE_LOCAL):
        """ Set a value in the a scope. """
        if where == Scope.SCOPE_LOCAL:
            self._local[name] = value
        elif where == Scope.SCOPE_GLOBAL:
            self._global[name] = value
        elif where == Scope.SCOPE_TEMPLATE:
            self._template[name] = value
        elif where == Scope.SCOPE_PRIVATE:
            self._private[name] = value
        else:
            # Shold never happen, but default to local
            self._scope._local[name] = value

    def update(self, values):
        """ Update values in the context. """
        self._local.update(values)

    def unset(self, name):
        """ Unset a variable from the current scope. """
        self._local.pop(name, None)
        self._private.pop(name, None)

    def clear(self):
        """ Clear the current context. """
        self._local.clear()
        self._private.clear()

    def get(self, var):
        """ Get a dotted variable. """

        # Find the scope dict it is in
        cur = self
        found = None

        while cur is not None:
            # Try private scope first
            if cur is self and var[0] in cur._private:
                found = cur._private
                break

            if var[0] in cur._local:
                found = cur._local
                break

            # Walk up the scopes
            cur = cur._parent

        if found is None:
            raise KeyError(var[0])

        # Solve dotted variables
        value = found[var[0]]
        for dot in var[1:]:

            if dot[0:1] == "#":
                # Requested direct dict item access
                try:
                    value = value[dot[1:]]
                except:
                    raise KeyError(dot)

            elif dot[0:1] == "@":
                # Requested direct attribute access
                try:
                    value = getattr(value, dot[1:])
                except:
                    raise KeyError(dot)

            else:
                # Try to acess the item both ways
                try:
                    value = value[dot]
                except:
                    try:
                        value = getattr(value, dot)
                    except:
                        raise KeyError(dot)

        return value


