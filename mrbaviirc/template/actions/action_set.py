""" Handler for the set action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument
# pylint: disable=missing-docstring

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node


class AssignNode(Node):
    """ Set a variable to a subvariable. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns

    def render(self, state):
        """ Set the value. """
        for (var, expr) in self.assigns:
            state.set_var(var[0], expr.eval(state), var[1])


def set_handler(parser, template, line, action, start, end):
    """ Parse the action """
    assigns = parser._parse_multi_assign(start, end, allow_type=True)

    node = AssignNode(template, line, assigns)
    parser.add_node(node)

ACTION_HANDLERS = {
    "set": set_handler,
}
