""" Html library for templates. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016-2019"
__license__     = "Apache License 2.0"


import cgi


class _HtmlLib(object):
    """ An HTML library for escaping values. """

    def esc(self, value, quote=False):
        """ Escape for HTML. """
        return cgi.escape(value, quote)


FACTORY = _HtmlLib
