""" Library of functions/objects for templates. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

__all__ = []


import sys
import importlib

from ..errors import UnknownVariableError, ParserError
from ..util import specialfunction


__all__.append("Library")
class Library:
    """ Base class for a library of functions.  While not required, it provides
        some utility for the function libraries. """

    def __getattr__(self, name):
        """ Load a sublibrary if an accessed attribute name ends in lib. """
        if name.endswith("lib"):
            module = sys.modules.get(self.__module__, None)
            if module is not None and module.__package__:
                submodule = importlib.import_module(module.__package__ + "." + name)
                factory = getattr(submodule, "FACTORY", None)
                if factory is not None:
                    lib = factory()
                    setattr(self, name, lib)
                    return lib

        # If we got here, library wasn't loaded
        raise AttributeError(name)


from .stdlib import StdLib
__all__.append("StdLib")


# The new library
#################


# Special functions

class _Defined(specialfunction):
    def __call__(self, env, template, line, scope, params):
        """ Return true if all params evaluate successfully. """
        try:
            _ = [param.eval(scope) for param in params]
            return True
        except (KeyError, IndexError, AttributeError, TypeError, UnknownVariableError):
            return False


class _Default(specialfunction):
    def __call__(self, env, template, line, scope, params):
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


# Standard library
##################

__all__.append("StandardLib")
class StandardLib(Library):
    """ Template library. """

    # Builtins
    defined = _Defined()
    default = _Default()

    @staticmethod
    def list(*args):
        return builtins.list(*args)

    @staticmethod
    def tuple(*args):
        return builtins.tuple(*args)

    @staticmethod
    def set(*args):
        return builtins.set(*args)

    @staticmethod
    def dict(*args):
        return builtins.dict(*args)

    @staticmethod
    def int(*args):
        return builtins.int(*args)

    @staticmethod
    def float(*args):
        return builtins.float(*args)

    @staticmethod
    def bool(*args):
        return builtins.bool(*args)

    @staticmethod
    def str(*args):
        return builtins.str(*args)

    @staticmethod
    def bytes(*args):
        return builtins.bytes(*args)

    @staticmethod
    def any(*args):
        return builtins.any(*args)

    @staticmethod
    def all(*args):
        return builtins.all(*args)

    @staticmethod
    def abs(*args):
        return builtins.abs(*args)

    @staticmethod
    def min(*args):
        return builtins.min(*args)

    @staticmethod
    def max(*args):
        return builtins.max(*args)

    @staticmethod
    def len(*args):
        return builtins.len(*args)

    @staticmethod
    def range(*args):
        return builtins.range(*args)

    @staticmethod
    def sorted(*args):
        return builtins.sorted(*args)

    @staticmethod
    def reversed(*args):
        return builtins.reversed(*args)

    @staticmethod
    def round(*args):
        return builtins.round(*args)

    @staticmethod
    def zip(*args):
        return builtins.zip(*args)
