""" Provide errors for the templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


class Error(Exception):
    """ Base template engine error. """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class RestrictedError(Error):
    """ Represent an restriction". """
    pass


class TemplateError(Error):
    """ An error at a specific location in atemplate file. """

    def __init__(self, message, filename, line):
        Error.__init__(self, "{0} on: {1}:{2}".format(
            message,
            filename if filename else "<string>",
            line
        ))
        self.filename = filename
        self.line = line


class SyntaxError(TemplateError):
    """ Represent a syntax error in the template. """
    pass


class UnknownVariableError(TemplateError):
    """ Represent an unknown variable access. """
    pass


class UnknownDefineError(TemplateError):
    """ Represent an unknown definition access. """
    pass


class UnknownIndexError(TemplateError):
    """ Represent an unknown index into a variable. """
    pass

class RaisedError(TemplateError):
    """ Represent an error raised from the template itself. """
    pass


