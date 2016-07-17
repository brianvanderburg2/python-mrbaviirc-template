# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides the exceptions used by the template engine.

__all__ = [
    "Error", "TemplateError", "SyntaxError", "UnknownVariableError",
    "UnknownFilterError", "UnknownDefineError"
]


class Error(Exception):
    """ Base template engine error. """
    def __init__(self, message):
        self.message = message


class TemplateError(Error):
    """ An error at a specific location in atemplate file. """
    MESSAGE_PREFIX = "Template Error"

    def __init__(self, message, filename, line):
        Error.__init__(self, "{0}: {1} on {2}:{3}".format(
            self.MESSAGE_PREFIX,
            message,
            filename if filename else "<string>",
            line
        ))
        self.filename = filename
        self.line = line


class SyntaxError(TemplateError):
    """ Represent a syntax error in the template. """
    MESSAGE_PREFIX = "Syntax Error"


class UnknownVariableError(TemplateError):
    """ Represent an unknown variable access. """
    MESSAGE_PREFIX = "Unknown Variable Error"


class UnknownFilterError(TemplateError):
    """ Represent an unknown filter access. """
    MESSAGE_PREFIX = "Unknown Filter Error"

class UnknownDefineError(TemplateError):
    """ Represent an unknown definition access. """
    MESSAGE_PREFIX = "Unknown Define Error"

