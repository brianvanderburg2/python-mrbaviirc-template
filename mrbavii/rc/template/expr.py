# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides the expression nodes used by the template engine.

from .errors import *


__all__ = [
    "Expr", "ValueExpr", "FilterExpr", "VarExpr"
]


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


class FilterExpr(Expr):
    """ An expression that represents a filter to call. """

    def __init__(self, template, line, node, filter, nodes):
        """ Initialize the filter expression. """
        Expr.__init__(self, template, line)
        self._node = node
        self._filter = filter
        self._nodes = nodes

    def eval(self):
        """ Evaluate the expression. """
        value = self._node.eval()

        params = []
        for node in self._nodes:
            params.append(node.eval())

        try:
            return self._env.filter(self._filter, value, *params)
        except KeyError:
            raise UnknownFilterError(
                self._filter,
                self._template._filename,
                self._line
            )

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
        except (KeyError, ValueError, TypeError, AttributeError):
            raise UnknownVariableError(
                ".".join(self._var),
                self._template._filename,
                self._line
            )


