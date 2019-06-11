""" Handler for the return action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node


class ReturnNode(Node):
    """ A node to set a return variable. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns

    def render(self, renderer, scope):
        """ Set the return nodes. """

        result = {}
        for (var, expr) in self.assigns:
            result[var] = expr.eval(scope)

        current = scope.template_scope.setdefault(":return:", {})
        current.update(result)


def return_handler(parser, template, line, action, start, end):
    """ Parse the action """
    assigns = parser._parse_multi_assign(start, end)

    node = ReturnNode(template, line, assigns)
    parser.add_node(node)


ACTION_HANDLERS = {"return": return_handler}
