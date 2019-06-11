""" Handler for the error action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node


class ErrorNode(Node):
    """ Raise an error from the template. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, renderer, scope):
        """ Raise the error. """
        raise RaisedError(
            str(self.expr.eval(scope)),
            self.template.filename,
            self.line
        )


def error_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = parser._parse_expr(start, end)

    node = ErrorNode(template, line, expr)
    parser.add_node(node)


ACTION_HANDLERS = {"error": error_handler}
