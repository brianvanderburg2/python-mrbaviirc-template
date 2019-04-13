""" Provide errors for the templates.

Classes
-------
Error
    Base exception for all template errors.
RestrictedError
    Exception raised when a restriction is encountered.
AbortError
    Exception raised during render when the render is aborted.
TemplateError
    Base exception related to template load and render issues.
ParserError
    Exception raised when a parsing error occurs during parsing a template
    such as an invalid template syntax.
UnknownVariableError
    Exception raised if an unknown variable or attribute is accessed within the
    template during a render.
UnknownIndexError
    Exception raised if an unknown index is accessed in a variable within the
    template during a render.
UnkownImportError
    Exception raised if a template attempts to import a library which has not
    been registered in the environment.
RaisedError
    Exception raised from the template in the error template tag.
"""

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


class Error(Exception):
    """ Base template engine error. """
    def __init__(self, message):
        """ Initialize the exception.

        Parameters
        ----------
        message : str
            The exception message.
        """
        Exception.__init__(self, message)
        self.message = message

    def __str__(self):
        """ Retrieve the message of the template.

        Return
        ------
        str
            The message passed to the exception constructor.
        """
        return self.message


class RestrictedError(Error):
    """ Represent an restriction". """
    pass


class AbortError(Error):
    """ Represent an aborted template render. """
    pass


class TemplateError(Error):
    """ An error at a specific location in atemplate file. """

    def __init__(self, message, filename, line):
        """ Initialze the template error.

        Parameters
        ----------
        message : str
            The base message, which will be joined with the filename and line
        filename : str
            The filename of the template where the error occured.
        line : int
            The line where the error occurred.
        """
        Error.__init__(self, "{0} on: {1}:{2}".format(
            message,
            filename if filename else "<string>",
            line
        ))
        self.filename = filename
        self.line = line


class ParserError(TemplateError):
    """ Represent a parsing syntax error in the template. """
    pass


class UnknownVariableError(TemplateError):
    """ Represent an unknown variable access. """
    pass


class UnknownIndexError(TemplateError):
    """ Represent an unknown index into a variable. """
    pass

class UnknownImportError(TemplateError):
    """ Represent an import of an unknown name. """
    pass

class RaisedError(TemplateError):
    """ Represent an error raised from the template itself. """
    pass
