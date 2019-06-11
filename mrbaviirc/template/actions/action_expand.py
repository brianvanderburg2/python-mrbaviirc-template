""" Handler for the expand action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node
from ..errors import ParserError


class ExpandNode(Node):
    """ A node to expand variables into the current scope. """

    def __init__(self, template, line, expr):
        """ Initialize """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, renderer, scope):
        """ Expand the variables. """

        result = self.expr.eval(scope)
        try:
            scope.update(result)
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
