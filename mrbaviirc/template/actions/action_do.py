""" Handler for the do action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import DoNode


def do_handler(parser, template, line, action, start, end):
    """ Parse the action """
    nodes = parser._parse_multi_expr(start, end)

    node = DoNode(template, line, nodes)
    parser.add_node(node)


ACTION_HANDLERS = {"do": do_handler}
