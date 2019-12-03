""" Handler for the switch action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node, NodeList
from ..errors import ParserError


class SwitchNode(Node):
    """ A node for basic if/elif/elif/else nesting. """
    types = ["lt", "le", "gt", "ge", "ne", "eq", "bt"]
    argc = [1, 1, 1, 1, 1, 1, 2]
    cbs = [
        lambda *args: args[0] < args[1],
        lambda *args: args[0] <= args[1],
        lambda *args: args[0] > args[1],
        lambda *args: args[0] >= args[1],
        lambda *args: args[0] != args[1],
        lambda *args: args[0] == args[1],
        lambda *args: args[0] >= args[1] and args[0] <= args[2]
    ]

    def __init__(self, template, line, expr):
        """ Initialize the switch node. """
        Node.__init__(self, template, line)
        self.expr = expr
        self.default_nodes = NodeList()
        self.cases_nodes = []
        self.nodes = self.default_nodes

    def add_case(self, testfunc, exprs):
        """ Add a case node. """
        self.cases_nodes.append((testfunc, NodeList(), exprs))
        self.nodes = self.cases_nodes[-1][1]

    def render(self, state):
        """ Render the node. """
        value = self.expr.eval(state)

        for testfunc, nodes, exprs in self.cases_nodes:
            params = [expr.eval(state) for expr in exprs]
            if testfunc(value, *params):
                return nodes.render(state)

        return self.default_nodes.render(state)


def switch_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = parser._parse_expr(start, end)

    node = SwitchNode(template, line, expr)
    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(switch_subhandler)

def switch_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """

    if action in SwitchNode.types:
        offset = SwitchNode.types.index(action)
        argc = SwitchNode.argc[offset]

        exprs = parser._parse_multi_expr(start, end)

        if len(exprs) != argc:
            raise ParserError(
                "Switch clause {0} takes {1} argument".format(action, argc),
                template.filename,
                line
            )

        node = parser.pop_nodestack()
        node.add_case(SwitchNode.cbs[offset], exprs)
        parser.push_nodestack(node.nodes)

    elif action == "endswitch":
        parser._get_no_more_tokens(start, end)
        parser.pop_nodestack()
        parser.pop_handler()

    else:
        parser.handle_action(parser, template, line, action, start, end)


ACTION_HANDLERS = {"switch": switch_handler}
