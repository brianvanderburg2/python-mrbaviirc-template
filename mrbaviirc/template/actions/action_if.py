""" Handler for the if action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler, DefaultActionHandler
from ..nodes import Node, NodeList


class IfNode(Node):
    """ A node that manages if/elif/else. """

    def __init__(self, template, line, expr):
        """ Initialize the if node. """
        Node.__init__(self, template, line)
        self.ifs_nodes = [(expr, NodeList())]
        self.else_nodes = None
        self.nodes = self.ifs_nodes[0][1]

    def add_elif(self, expr):
        """ Add an if section. """
        # TODO: error if self.elses exists
        self.ifs_nodes.append((expr, NodeList()))
        self.nodes = self.ifs_nodes[-1][1]

    def add_else(self):
        """ Add an else. """
        self.else_nodes = NodeList()
        self.nodes = self.else_nodes

    def render(self, state):
        """ Render the if node. """
        for (expr, nodes) in self.ifs_nodes:
            result = expr.eval(state)
            if result:
                return nodes.render(state)

        if self.else_nodes:
            return self.else_nodes.render(state)


class IfActionHandler(ActionHandler):
    """ Handle the if action """

    def handle_action_if(self, line, start, end):
        expr = self.parser.parse_expr(start, end)
        node = IfNode(self.template, line, expr)

        self.parser.add_node(node)
        self.parser.push_nodestack(node.nodes)
        self.parser.push_handler(IfSubHandler(self.parser, self.template))


class IfSubHandler(DefaultActionHandler):
    """ Handle stuff under if """

    def handle_action_elif(self, line, start, end):
        """ elif """
        expr = self.parser.parse_expr(start, end)
        node = self.parser.pop_nodestack()
        node.add_elif(expr)
        self.parser.push_nodestack(node.nodes)

    def handle_action_else(self, line, start, end):
        """ else """
        self.parser.get_no_more_tokens(start, end)
        node = self.parser.pop_nodestack()
        node.add_else()
        self.parser.push_nodestack(node.nodes)

    def handle_action_endif(self, line, start, end):
        """ endif """
        self.parser.get_no_more_tokens(start, end)
        self.parser.pop_nodestack()
        self.parser.pop_handler()


ACTION_HANDLERS = {"if": IfActionHandler}
