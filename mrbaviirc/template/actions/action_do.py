""" Handler for the do action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument
__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node


class DoNode(Node):
    """ Evaluate expressions and discard the results. """

    def __init__(self, template, line, exprs):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.exprs = exprs

    def render(self, state):
        """ Set the value. """
        for expr in self.exprs:
            expr.eval(state)


class DoActionHandler(ActionHandler):
    """ Handle the do action. """

    def handle_action_do(self, line, start, end):
        """ Handle the do action. """
        nodes = self.parser._parse_multi_expr(start, end)

        node = DoNode(self.template, line, nodes)
        self.parser.add_node(node)


ACTION_HANDLERS = {"do": DoActionHandler}
