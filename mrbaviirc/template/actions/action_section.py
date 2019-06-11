""" Handler for the section action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node, NodeList
from ..errors import ParserError


class SectionNode(Node):
    """ A node to redirect template output to a section. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr
        self.nodes = NodeList()

    def render(self, renderer, scope):
        """ Redirect output to a section. """

        section = str(self.expr.eval(scope))
        renderer.push_section(section)
        self.nodes.render(renderer, scope)
        renderer.pop_section()


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
