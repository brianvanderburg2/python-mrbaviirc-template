""" Handler for the unset action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import UnsetNode


def unset_handler(parser, template, line, action, start, end):
    """ Parse the action """
    varlist = parser._parse_multi_var(start, end)

    node = UnsetNode(template, line, varlist)
    parser.add_node(node)


ACTION_HANDLERS = {"unset": unset_handler}
