""" Handler for the var action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler, DefaultActionHandler
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

        new_renderer = state.push_renderer()
        try:
            self.nodes.render(state)
            contents = new_renderer.get()
            state.set_var(self.var[0], contents, self.var[1])
        finally:
            state.pop_renderer()


class VarActionHandler(ActionHandler):
    """ Handle var """

    def handle_action_var(self, line, start, end):
        """ Handle var """
        var = self.parser.get_token_var(start, end, allow_type=True)
        start += 1

        self.parser.get_no_more_tokens(start, end)

        node = VarNode(self.template, line, var)
        self.parser.add_node(node)
        self.parser.push_nodestack(node.nodes)
        self.parser.push_handler(VarSubHandler(self.parser, self.template))


class VarSubHandler(DefaultActionHandler):
    """ Handle items under var """

    def handle_action_endvar(self, line, start, end):
        """ endvar """
        self.parser.get_no_more_tokens(start, end)
        self.parser.pop_nodestack()
        self.parser.pop_handler()


ACTION_HANDLERS = {"var": VarActionHandler}
