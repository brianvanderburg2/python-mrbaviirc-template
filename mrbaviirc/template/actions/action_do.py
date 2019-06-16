""" Handler for the do action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument
__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node


class DoNode(Node):
    """ Evaluate expressions and discard the results. """

    def __init__(self, template, line, exprs):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.exprs = exprs

    def render(self, renderer, scope):
        """ Set the value. """
        for expr in self.exprs:
            expr.eval(scope)


def do_handler(parser, template, line, action, start, end):
    """ Parse the action """
    nodes = parser._parse_multi_expr(start, end)

    node = DoNode(template, line, nodes)
    parser.add_node(node)


ACTION_HANDLERS = {"do": do_handler}
