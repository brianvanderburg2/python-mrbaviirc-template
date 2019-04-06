""" Handler for the error action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import ErrorNode


def error_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = parser._parse_expr(start, end)

    node = ErrorNode(template, line, expr)
    parser.add_node(node)


ACTION_HANDLERS = {"error": error_handler}
