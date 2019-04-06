""" Handler for the if action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import IfNode
from ..errors import SyntaxError


def if_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = parser._parse_expr(start, end)
    node = IfNode(template, line, expr)

    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(if_subhandler)


def if_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """
    
    if action == "elif":
        expr = parser._parse_expr(start, end)
        node = parser.pop_nodestack()
        node.add_elif(expr)
        parser.push_nodestack(node.nodes)

    elif action == "else":
        parser._get_no_more_tokens(start, end)
        node = parser.pop_nodestack()
        node.add_else()
        parser.push_nodestack(node.nodes)

    elif action == "endif":
        parser._get_no_more_tokens(start, end)
        parser.pop_nodestack()
        parser.pop_handler()

    else:
        parser.handle_action(parser, template, line, action, start, end)


ACTION_HANDLERS = {"if": if_handler}
