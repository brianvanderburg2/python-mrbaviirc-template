""" Handler for the error action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..errors import RaisedError
from ..nodes import Node


class ErrorNode(Node):
    """ Raise an error from the template. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, state):
        """ Raise the error. """
        raise RaisedError(
            str(self.expr.eval(state)),
            self.template.filename,
            self.line
        )


class ErrorActionHandler(ActionHandler):
    """ Handle the error action. """

    def handle_action_error(self, line, start, end):
        expr = self.parser.parse_expr(start, end)

        node = ErrorNode(self.template, line, expr)
        self.parser.add_node(node)


ACTION_HANDLERS = {"error": ErrorActionHandler}
