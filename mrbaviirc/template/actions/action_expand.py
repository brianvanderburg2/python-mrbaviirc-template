""" Handler for the expand action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node
from ..errors import TemplateError


class ExpandNode(Node):
    """ A node to expand variables into the local variables. """

    def __init__(self, template, line, expr):
        """ Initialize """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, state):
        """ Expand the variables. """

        result = self.expr.eval(state)
        try:
            state.update_vars(result)
        except (KeyError, TypeError, ValueError) as error:
            raise TemplateError(
                str(error),
                self.template.filename,
                self.line
            )


def expand_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = parser._parse_expr(start, end)

    node = ExpandNode(template, line, expr)
    parser.add_node(node)


ACTION_HANDLERS = {"expand": expand_handler}
