""" Handler for the return action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import ReturnNode


def return_handler(parser, template, line, action, start, end):
    """ Parse the action """
    assigns = parser._parse_multi_assign(start, end)

    node = ReturnNode(template, line, assigns)
    parser.add_node(node)


ACTION_HANDLERS = {"return": return_handler}
