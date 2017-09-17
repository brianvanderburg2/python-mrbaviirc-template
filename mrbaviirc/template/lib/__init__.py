""" Library of functions/objects for templates. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

__all__ = []


__all__.append("Library")
class Library(object):
    """ Represent a library of functions.  Originally used to provide helpers
        for accessing attributes.  This function has been moved directly to
        Environment.get and the use of this as a base class is now obsolete.
    """
    pass


from .stdlib import StdLib
__all__.append("StdLib")
