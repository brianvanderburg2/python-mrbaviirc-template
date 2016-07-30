""" Provide expressions for the templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "MIT"

__all__ = [
    "Expr", "ValueExpr", "FuncExpr", "ListExpr", "VarExpr"
]


from .errors import *


class Expr(object):
    """ Base for an expression object. """

    def __init__(self, template, line):
        """ Initialize the expression object. """
        self._template = template
        self._env = template._env
        self._line = line

    def eval(self):
        """ Evaluate the expression object. """
        raise NotImplementedError


class ValueExpr(Expr):
    """ An expression that represents a value. """

    def __init__(self, template, line, value):
        """ Initialize the value expression. """
        Expr.__init__(self, template, line)
        self._value = value

    def eval(self):
        """ Evaluate the expression. """
        return self._value


class FuncExpr(Expr):
    """ A function expression node. """

    def __init__(self, template, line, var, nodes):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self._var = var
        self._nodes = nodes

    def eval(self):
        """ Evaluate the expression. """
        try:
            fn = self._env.get(self._var)
            params = [node.eval() for node in self._nodes]
            return fn(*params)
        except KeyError:
            raise UnknownVariableError(
                ".".join(self._var),
                self._template._filename,
                self._line
            )


class ListExpr(Expr):
    """ A list expression node. """
    
    def __init__(self, template, line, nodes):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self._nodes = nodes

    def eval(self):
        """ Evaluate the expression. """
        return [node.eval() for node in self._nodes]


class VarExpr(Expr):
    """ An expression that represents a variable. """

    def __init__(self, template, line, var):
        """ Initialize the variable expression. """
        Expr.__init__(self, template, line)
        self._var = var

    def eval(self):
        """ Evaluate the expression. """
        try:
            return self._env.get(self._var)
        except KeyError:
            raise UnknownVariableError(
                ".".join(self._var),
                self._template._filename,
                self._line
            )


