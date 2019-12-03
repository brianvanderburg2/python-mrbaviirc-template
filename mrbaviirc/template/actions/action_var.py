""" Handler for the var action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node, NodeList
from ..renderers import StringRenderer


class VarNode(Node):
    """ Capture output into a variable. """

    def __init__(self, template, line, var):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.var = var
        self.nodes = NodeList()

    def render(self, state):
        """ Render the results and capture into a variable. """

        try:
            original_renderer = state.renderer
            state.renderer = StringRenderer()
            self.nodes.render(state)
            state.set_var(self.var[0], state.renderer.get(), self.var[1])
        finally:
            state.renderer = original_renderer


def var_handler(parser, template, line, action, start, end):
    """ Parse the action """
    var = parser._get_token_var(start, end, allow_type=True)
    start += 1

    parser._get_no_more_tokens(start, end)

    node = VarNode(template, line, var)
    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(var_subhandler)


def var_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """

    if action == "endvar":
        parser._get_no_more_tokens(start, end)
        parser.pop_nodestack()
        parser.pop_handler()

    else:
        parser.handle_action(parser, template, line, action, start, end)


ACTION_HANDLERS = {"var": var_handler}
