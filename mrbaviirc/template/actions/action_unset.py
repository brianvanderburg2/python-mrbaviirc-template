""" Handler for the unset action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node


class UnsetNode(Node):
    """ Unset variable at the current scope rsults. """

    def __init__(self, template, line, varlist):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.varlist = varlist

    def render(self, renderer, scope):
        """ Set the value. """
        for item in self.varlist:
            scope.unset(item)


def unset_handler(parser, template, line, action, start, end):
    """ Parse the action """
    varlist = parser._parse_multi_var(start, end)

    node = UnsetNode(template, line, varlist)
    parser.add_node(node)


ACTION_HANDLERS = {"unset": unset_handler}
