""" Provide expressions for the templates. """

# pylint: disable=too-few-public-methods,too-many-arguments

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"

__all__ = [
    "Expr", "ValueExpr", "FuncExpr", "ListExpr", "DictExpr", "VarExpr",
    "LookupAttrExpr", "LookupItemExpr", "LookupSliceExpr", "BooleanBinaryExpr",
    "BinaryExpr", "BooleanUnaryExpr", "UnaryExpr"
]


from .errors import UnknownVariableError, UnknownIndexError


class Expr(object):
    """ Base for an expression object. """

    def __init__(self, template, line):
        """ Initialize the expression object. """
        self.template = template
        self.line = line

    def eval(self, scope):
        """ Evaluate the expression object. """
        raise NotImplementedError


class ValueExpr(Expr):
    """ An expression that represents a value.
        This should be used only for immutable values since assigment simply
        returns the value.  Else a template item may mutate the value in the
        node and a later assigmnet may have an unexpcted value.
    """

    def __init__(self, template, line, value):
        """ Initialize the value expression. """
        Expr.__init__(self, template, line)
        self.value = value

    def eval(self, scope):
        """ Evaluate the expression. """
        return self.value


class FuncExpr(Expr):
    """ A function expression node. """

    def __init__(self, template, line, expr, nodes):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.expr = expr
        self.nodes = nodes

    def eval(self, scope):
        """ Evaluate the expression. """
        func = self.expr.eval(scope)
        if hasattr(func, "_is_mrbaviirc_template_special"):
            return func(
                self.template.env,
                self.template,
                self.line,
                scope,
                self.nodes
            )
        else:
            params = [node.eval(scope) for node in self.nodes]
            return func(*params)


class ListExpr(Expr):
    """ A list expression node. """

    def __init__(self, template, line, nodes):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.nodes = nodes

    def eval(self, scope):
        """ Evaluate the expression. """
        return [node.eval(scope) for node in self.nodes]


class DictExpr(Expr):
    """ A dict expression node. """

    def __init__(self, template, line, key_nodes, value_nodes):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.key_nodes = key_nodes
        self.value_nodes = value_nodes

    def eval(self, scope):
        """ Evaluate the expression. """
        return dict(zip(
            (key.eval(scope) for key in self.key_nodes),
            (value.eval(scope) for value in self.value_nodes)
        ))


class VarExpr(Expr):
    """ An expression that represents a variable. """

    def __init__(self, template, line, var):
        """ Initialize the variable expression. """
        Expr.__init__(self, template, line)
        self.var = var

    def eval(self, scope):
        """ Evaluate the expression. """
        try:
            return scope.get(self.var)
        except KeyError:
            raise UnknownVariableError(
                self.var,
                self.template.filename,
                self.line
            )


class LookupAttrExpr(Expr):
    """ An array index expression node. """

    def __init__(self, template, line, expr, attr):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.expr = expr
        self.attr = attr

    def eval(self, scope):
        """ Evaluate the expression. """
        result = self.expr.eval(scope)
        try:
            return getattr(result, self.attr)
        except (TypeError, KeyError, IndexError, AttributeError):
            raise UnknownVariableError(
                self.attr,
                self.template.filename,
                self.line
            )


class LookupItemExpr(Expr):
    """ An array index expression node. """

    def __init__(self, template, line, expr, item):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.expr = expr
        self.item = item

    def eval(self, scope):
        """ Evaluate the expression. """
        result = self.expr.eval(scope)
        item = self.item.eval(scope)
        try:
            return result[item]
        except (KeyError, IndexError, TypeError):
            raise UnknownIndexError(
                item,
                self.template.filename,
                self.line
            )


class LookupSliceExpr(Expr):
    """ An array index expression node. """

    def __init__(self, template, line, expr, items):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.expr = expr
        self.items = items

    def eval(self, scope):
        """ Evaluate the expression. """
        result = self.expr.eval(scope)
        # Eval each slice item
        parts = list(item.eval(scope) if item is not None else None for item in self.items)
        parts.extend([None, None, None]) # Ensure at least 3 parts
        (p0, p1, p2) = parts[0:3]

        try:
            return result[slice(p0, p1, p2)]
        except (KeyError, IndexError, TypeError):
            raise UnknownIndexError(
                "{0},{1},{2}".format(str(p0), str(p1), str(p2)),
                self.template.filename,
                self.line
            )

class BooleanBinaryExpr(Expr):
    """ Return boolean binary operation of two expressions. """
    def __init__(self, template, line, oper, expr1, expr2):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.oper = oper
        self.expr1 = expr1
        self.expr2 = expr2

    def eval(self, scope):
        """ Evaluate the expression. """

        return bool(self.oper(
            self.expr1.eval(scope),
            self.expr2.eval(scope)
        ))


class BinaryExpr(Expr):
    """ Return binary operation of two expressions. """
    def __init__(self, template, line, oper, expr1, expr2):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.oper = oper
        self.expr1 = expr1
        self.expr2 = expr2

    def eval(self, scope):
        """ Evaluate the expression. """

        return self.oper(
            self.expr1.eval(scope),
            self.expr2.eval(scope)
        )


class BooleanUnaryExpr(Expr):
    """ Return boolean binary operation of two expressions. """
    def __init__(self, template, line, oper, expr1):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.oper = oper
        self.expr1 = expr1

    def eval(self, scope):
        """ Evaluate the expression. """

        return bool(self.oper(self.expr1.eval(scope)))


class UnaryExpr(Expr):
    """ Return binary operation of two expressions. """
    def __init__(self, template, line, oper, expr1):
        """ Initialize the node. """
        Expr.__init__(self, template, line)
        self.oper = oper
        self.expr1 = expr1

    def eval(self, scope):
        """ Evaluate the expression. """

        return self.oper(self.expr1.eval(scope))
