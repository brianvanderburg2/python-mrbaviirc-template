""" The module provides the builtin values to the template engine. """
# pylint: disable=unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"

__all__ = ["context"]


from ..errors import UnknownVariableError, ParserError
from ..util import specialfunc


context = {} # pylint: disable=invalid-name
def _builtin(func_or_name):
    """ Decorator to add a function to the builtin dict. """
    if isinstance(func_or_name, str):
        def wrapper(func): # pylint: disable=missing-docstring
            context[func_or_name] = func
            return func
        return wrapper
    else:
        context[func_or_name.__name__] = func_or_name
        return func_or_name


@_builtin
@specialfunc
def defined(env, template, line, scope, params):
    """ Return true if all params evaluate successfully. """
    try:
        _ = [param.eval(scope) for param in params]
        return True
    except (KeyError, IndexError, AttributeError, TypeError, UnknownVariableError):
        return False


@_builtin
@specialfunc
def default(env, template, line, scope, params):
    """ Return a default if the first parameter does not evaluate. """
    if len(params) != 2:
        raise ParserError(
            "Template builting 'default' expects 2 arguments",
            template,
            line
        )

    try:
        return params[0].eval(scope)
    except (KeyError, IndexError, AttributeError, TypeError, UnknownVariableError):
        return params[1].eval(scope)
