""" Provide errors for the templates. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


class Error(Exception):
    """ Base template engine error.

    This is the base error class for any errors that are geneted directly by
    the template engine or captured and reraised as a template engine error.

    Attributes
    ----------
    message : str
        The exception message.
    """

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
    """ Represent an restriction.

    This exception is raised when restriction-related errors occur such as
    accessing a template outside of the template path or using a code section
    when code usage is disabled.
    """
    pass


class AbortError(Error):
    """ Represent an aborted template render. """
    pass


class TemplateError(Error):
    """ An error at a specific location in atemplate file.

    Attributes
    ----------
    filename : str
        The filename of the template where the error occured.
    line : int
        The line where the error occured.
    """

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
