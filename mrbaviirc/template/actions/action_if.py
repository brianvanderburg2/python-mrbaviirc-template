""" Handler for the if action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


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
