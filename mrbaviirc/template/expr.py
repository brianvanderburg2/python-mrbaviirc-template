""" Internal use only.  Provide expression notes for the templates. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"

__all__ = [
    "Expr", "ValueExpr", "FuncExpr", "ListExpr", "DictExpr", "VarExpr",
    "LookupAttrExpr", "LookupItemExpr", "LookupSliceExpr", "BooleanBinaryExpr",
    "BinaryExpr", "AndExpr", "OrExpr", "BooleanUnaryExpr", "UnaryExpr"
]


import weakref

from .errors import UnknownVariableError, UnknownIndexError
from .util import specialfunction


class Expr:
    """ Base for an expression object. """

    def __init__(self, template, line):
        """ Initialize the expression object.

        Parameters
        ----------
        template : mrbaviirc.template.Template
            The template object this expression node is a member of.
            The template is stored as a weak reference as to prevent
            circular references.
        line : int
            The line number of the template that this expression is at.
        """
        self._template = weakref.ref(template)
        self.line = line

    @property
    def template(self):
        """ Return the referenced template.

        Returns
        -------
        mrbaviirc.template.Template
            The template object that this expression node is a member of.
        None
            If the weak reference to the template node is destroyed. This is
            unlikely as an expressoin is only evaluated during render, during
            which the code calling a template render would have a reference
            to the template it is rendering.
        """
        return self._template()

    def eval(self, state):
        """ Evaluate the expression object.

        This must be implemented by derived classes.

        Parameters
        ----------
        state : mrbaviirc.template.state.RenderState
            The current template state

        Returns
        -------
        Any
            The return value depends on the type of expressoin node evaluated.
        """
        raise NotImplementedError


class ValueExpr(Expr):
    """ An expression that represents a value.
        This should be used only for immutable values since assigment simply
        returns the value.  Else a template item may mutate the value in the
        node and a later assigmnet may have an unexpcted value.
    """

    def __init__(self, template, line, value):
        """ Initialize the value expression.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        value : Any
            The value the expression node contains.
        """
        Expr.__init__(self, template, line)
        self.value = value

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        The value of the expression node.
        """
        return self.value


class FuncExpr(Expr):
    """ A function expression node. """

    def __init__(self, template, line, expr, nodes):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        expr : mrbaviirc.template.expr.Expr
            The result of this expression node is used as the function to call
        nodes : list or tuple
            A sequence of (str, mrbaviirc.template.expr.Expr) elements used to
            pass to the function call.  This sequence is unpacked as into
            (name, value) pairs. Pairs with a name value of None are used as
            positional parameters. Other pairs are used as keyword parameters.
        """
        Expr.__init__(self, template, line)
        self.expr = expr
        self.nodes = list(expr for (var, expr) in nodes if var is None)
        self.namednodes = list((var, expr) for (var, expr) in nodes if var is not None)

    def eval(self, state):
        """ Evaluate the function call and return the results.

        If the function evaluates to an instance of a class derived from
        mrbaviirc.template.util.sepcialfunction, then the the function call
        directly passes the state and the unevaluated parameter nodes.  This
        allows for creation of special functions that can catch exceptions in
        evaluation of paremters and return a result accordingly.

        In other cases, the function is called with the parameters from the
        template evaluated then passed, without any state object.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        Any
            The return value of the called funcion

        Raises
        ------
        Any
            As this can call any function available within the template's
            variables, any exception may be raised from within those functions.
        """
        func = self.expr.eval(state)
        if isinstance(func, specialfunction):
            state.line = self.line
            return func(state, self.nodes)

        params = [node.eval(state) for node in self.nodes]
        namedparams = {var: node.eval(state) for (var, node) in self.namednodes}
        return func(*params, **namedparams)


class ListExpr(Expr):
    """ A list expression node. """

    def __init__(self, template, line, nodes):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        nodes : list or tuple
            A sequence of mrbaviirc.template.expr.Expr nodes.

        """
        Expr.__init__(self, template, line)
        self.nodes = nodes

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        list
            The list of evaluated items.
        """
        return [node.eval(state) for node in self.nodes]


class DictExpr(Expr):
    """ A dict expression node. """

    def __init__(self, template, line, key_nodes, value_nodes):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        key_nodes : list or tuple
            A sequence of mrbaviirc.template.expr.Expr elements used to evaluate
            key names.
        value_nodes : list or tuple
            A sequence of mrbaviirc.template.expr.Expr elements used to evaluate
            key values
        """
        Expr.__init__(self, template, line)
        self.key_nodes = key_nodes
        self.value_nodes = value_nodes

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        A dictionary containing the key to value results from evaluating the
        pairs of keys and values.
        """
        return dict(zip(
            (key.eval(state) for key in self.key_nodes),
            (value.eval(state) for value in self.value_nodes)
        ))


class VarExpr(Expr):
    """ An expression that represents a variable. """

    def __init__(self, template, line, var):
        """ Initialize the variable expression.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        var : str
            The name of the variable to evaluate
        """
        Expr.__init__(self, template, line)
        self.var = var

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        Any
            The value of the variable found within the state

        Raises
        ------
        mrbaviirc.template.errors.UnknownVariableError
            If the variable was not found in the state
        """
        try:
            return state.get_var(self.var[0], self.var[1])
        except KeyError:
            raise UnknownVariableError(
                self.var,
                self.template.filename,
                self.line
            )


class LookupAttrExpr(Expr):
    """ An array index expression node. """

    def __init__(self, template, line, expr, attr):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        expr : mrbaviirc.template.expr.Expr
            The expression node to evaluate and find the attribute in
        attr : str
            The name of the attribute
        """
        Expr.__init__(self, template, line)
        self.expr = expr
        self.attr = attr

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        Any
            The expression object is first evaluated. Then the attribute is
            looked up within the object and returned if it exists.

        Raises
        ------
        mrbaviirc.template.errors.UnknownVariableError
            If the attribute could not be found
        """
        result = self.expr.eval(state)
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
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        expr : mrbaviirc.template.expr.Expr
            Expression whose result is the object to look up the item in
        item : mrbaviirc.template.expr.Expr
            Expression whose result is the index or key to look up
        """
        Expr.__init__(self, template, line)
        self.expr = expr
        self.item = item

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        Any
            First both expressions passed to the constructor are evaluated.
            Then the item expression's result is used as the key to look up
            in the expr expression's result.

        Raises
        ------
        mrbaviirc.template.errors.UnknownIndexError
            If the key or index is not found in the object.
        """
        result = self.expr.eval(state)
        item = self.item.eval(state)
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
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        expr : mrbaviirc.template.expr.Expr
            Expression whose result is used as the object to look in
        items : list
            A sequence of 3 items of mrbaviirc.template.expr.Expr used as the
            start, stop, and step values in the slice.
        """
        Expr.__init__(self, template, line)
        self.expr = expr
        self.items = items

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        Any
            The results of the evaluation of the items list is used to create a
            slice object which is then used to look up in the result of the expr
            evaluation.  The result of that lookup is returned

        Raises
        ------
        UnknownIndexError
            Raised if the slice lookup failed.

        """
        result = self.expr.eval(state)
        # Eval each slice item
        parts = list(item.eval(state) if item is not None else None for item in self.items)
        parts.extend([None, None, None]) # Ensure at least 3 parts
        (start, stop, step) = parts[0:3]

        try:
            return result[slice(start, stop, step)]
        except (KeyError, IndexError, TypeError):
            raise UnknownIndexError(
                "{0},{1},{2}".format(str(start), str(stop), str(step)),
                self.template.filename,
                self.line
            )

class BooleanBinaryExpr(Expr):
    """ Return boolean binary operation of two expressions. """

    def __init__(self, template, line, oper, expr1, expr2):

        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        oper : callable
            The callable to pass the results to
        expr1 : mrbaviirc.template.expr.Expr
            The left expression
        expr2 : mrbaviirc.template.expr.Expr
            The right expression
        """
        Expr.__init__(self, template, line)
        self.oper = oper
        self.expr1 = expr1
        self.expr2 = expr2

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        bool
            The operator is called on the results of both evaluated expressoins
            and the result is returned as a bool
        """

        return bool(self.oper(
            self.expr1.eval(state),
            self.expr2.eval(state)
        ))


class BinaryExpr(Expr):
    """ Return binary operation of two expressions. """

    def __init__(self, template, line, oper, expr1, expr2):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        oper : callable
            The callable to pass the results to
        expr1 : mrbaviirc.template.expr.Expr
            The left expression
        expr2 : mrbaviirc.template.expr.Expr
            The right expression
        """
        Expr.__init__(self, template, line)
        self.oper = oper
        self.expr1 = expr1
        self.expr2 = expr2

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        Any
            The operator is called on the results of both evaluated expressions
            and the result is returned directly.
        """

        return self.oper(
            self.expr1.eval(state),
            self.expr2.eval(state)
        )


class AndExpr(Expr):
    """ Return boolean AND of two expressions.

    This used instead of BinaryExpr to allow for shortcut evaluation. """

    def __init__(self, template, line, expr1, expr2):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        expr1 : mrbaviirc.template.expr.Expr
            The left expression
        expr2 : mrbaviirc.template.expr.Expr
            The right expression
        """
        Expr.__init__(self, template, line)
        self.expr1 = expr1
        self.expr2 = expr2

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        bool
            The first expression is evaluated. If it's boolean value is True
            then the second expression is evaluated.  The boolean result is
            returned and will only be True if both expressions evaluated to a
            True value.
        """

        result = self.expr1.eval(state)
        if result:
            result = self.expr2.eval(state)

        return bool(result)


class OrExpr(Expr):
    """ Return boolean OR of two expressions.

    This used instead of BinaryExpr to allow for shortcut evaluation. """

    def __init__(self, template, line, expr1, expr2):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        expr1 : mrbaviirc.template.expr.Expr
            The left expression
        expr2 : mrbaviirc.template.expr.Expr
            The right expression
        """
        Expr.__init__(self, template, line)
        self.expr1 = expr1
        self.expr2 = expr2

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        bool
            The first expression is evaluated. If it's boolean value is not True
            then the second expression is evaluated.  The boolean result is
            returned and will be True if at least one expression evaluated to a
            True value.
        """

        result = self.expr1.eval(state)
        if not result:
            result = self.expr2.eval(state)

        return bool(result)


class BooleanUnaryExpr(Expr):
    """ Return boolean binary operation of two expressions. """

    def __init__(self, template, line, oper, expr1):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        oper : callable
            The callable to pass the result to
        expr1 : mrbaviirc.template.expr.Expr
            The expression to evaluate and operate on
        """
        Expr.__init__(self, template, line)
        self.oper = oper
        self.expr1 = expr1

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        bool
            The expression is evaluated, is results passed to the callable, and
            the results returned as a boolean.

        """

        return bool(self.oper(self.expr1.eval(state)))


class UnaryExpr(Expr):
    """ Return binary operation of two expressions. """
    def __init__(self, template, line, oper, expr1):
        """ Initialize the node.

        Parameters
        ----------
        template
            See parent class
        line
            See parent class
        oper : callable
            The callable to pass the result to
        expr1 : mrbaviirc.template.expr.Expr
            The expression to evaluate and operate on
        """
        Expr.__init__(self, template, line)
        self.oper = oper
        self.expr1 = expr1

    def eval(self, state):
        """ Evaluate the expression.

        Parameters
        ----------
        state
            See parent class

        Returns
        -------
        bool
            The expression is evaluated, is results passed to the callable, and
            the results returned directly.
        """

        return self.oper(self.expr1.eval(state))
