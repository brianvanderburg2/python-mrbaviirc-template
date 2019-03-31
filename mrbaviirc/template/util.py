""" Utility functionsTokenize the input."""
# pylint: disable=too-few-public-methods,too-many-branches,too-many-statements

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"

__all__ = ["specialfunc"]


def specialfunc(func):
    """ Create a special callable function from a regular function. """
    func._is_mrbaviirc_template_special = True
    return func
