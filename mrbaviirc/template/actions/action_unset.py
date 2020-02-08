""" Handler for the unset action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node


class UnsetNode(Node):
    """ Unset variables. """

    def __init__(self, template, line, varlist):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.varlist = varlist

    def render(self, state):
        """ Set the value. """
        for item in self.varlist:
            state.unset_var(item[0], item[1])


class UnsetActionHandler(ActionHandler):
    """ Handle unset """

    def handle_action_unset(self, line, start, end):
        """ Handle unset """
        varlist = self.parser._parse_multi_var(start, end, allow_type=True)

        node = UnsetNode(self.template, line, varlist)
        self.parser.add_node(node)


ACTION_HANDLERS = {"unset": UnsetActionHandler}
