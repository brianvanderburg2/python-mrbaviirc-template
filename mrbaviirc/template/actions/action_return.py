""" Handler for the return action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node


class ReturnNode(Node):
    """ A node to set a return variable. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns

    def render(self, state):
        """ Set the return nodes. """

        result = {}
        for (var, expr) in self.assigns:
            result[var] = expr.eval(state)

        state.update_vars(result, state.RETURN_VAR)


class ReturnActionHandler(ActionHandler):
    """ Handle return """

    def handle_action_return(self, line, start, end):
        """ Handle return """
        assigns = self.parser.parse_multi_assign(start, end)

        node = ReturnNode(self.template, line, assigns)
        self.parser.add_node(node)


ACTION_HANDLERS = {"return": ReturnActionHandler}
