""" Handler for the section action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler, DefaultActionHandler
from ..nodes import Node, NodeList
from ..errors import ParserError


class SectionNode(Node):
    """ A node to redirect template output to a section. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr
        self.nodes = NodeList()

    def render(self, state):
        """ Capture output to a section.

            Multiple outputs to the same section append the results
        """

        section = str(self.expr.eval(state))
        new_renderer = state.push_renderer()
        try:
            self.nodes.render(state)
            contents = new_renderer.get()

            state.append_section(section, contents)
        finally:
            state.pop_renderer()


class SectionActionHandler(ActionHandler):
    """ Handle section """

    def handle_action_section(self, line, start, end):
        """ Handle section """
        expr = self.parser.parse_expr(start, end)

        node = SectionNode(self.template, line, expr)
        self.parser.add_node(node)
        self.parser.push_nodestack(node.nodes)
        self.parser.push_handler(SectionSubHandler(self.parser, self.template))


class SectionSubHandler(DefaultActionHandler):
    """ Handle inside of section. """

    def handle_action_endsection(self, line, start, end):
        """ End section """
        self.parser.get_no_more_tokens(start, end)
        self.parser.pop_nodestack()
        self.parser.pop_handler()


ACTION_HANDLERS = {"section": SectionActionHandler}
