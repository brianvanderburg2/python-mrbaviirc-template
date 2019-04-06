""" Handler for the section action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import SectionNode
from ..errors import SyntaxError


def section_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = parser._parse_expr(start, end)

    node = SectionNode(template, line, expr)
    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(section_subhandler)


def section_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """
    
    if action == "endsection":
        parser._get_no_more_tokens(start, end)
        parser.pop_nodestack()
        parser.pop_handler()

    else:
        parser.handle_action(parser, template, line, action, start, end)


ACTION_HANDLERS = {"section": section_handler}
