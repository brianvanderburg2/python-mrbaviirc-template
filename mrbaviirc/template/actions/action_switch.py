""" Handler for the switch action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler, DefaultActionHandler
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


class SwitchActionHandler(ActionHandler):
    """ Handle switch """

    def handle_action_switch(self, line, start, end):
        """ Handle switch """
        expr = self.parser.parse_expr(start, end)

        node = SwitchNode(self.template, line, expr)
        self.parser.add_node(node)
        self.parser.push_nodestack(node.nodes)
        self.parser.push_handler(SwitchSubHandler(self.parser, self.template))


class SwitchSubHandler(DefaultActionHandler):
    """ Handle inside of switch. """

    def handle_unknown_action(self, line, action, start, end):
        # override handle_action
        """ Handle nested tags """

        if action in SwitchNode.types:
            offset = SwitchNode.types.index(action)
            argc = SwitchNode.argc[offset]

            exprs = self.parser.parse_multi_expr(start, end)

            if len(exprs) != argc:
                raise ParserError(
                    "Switch clause {0} takes {1} argument".format(action, argc),
                    self.template.filename,
                    line
                )

            node = self.parser.pop_nodestack()
            node.add_case(SwitchNode.cbs[offset], exprs)
            self.parser.push_nodestack(node.nodes)

        else:
            DefaultActionHandler.handle_unknown_action(self, line, action, start, end)

    def handle_action_endswitch(self, line, start, end):
        """ Handle endswitch """
        self.parser.get_no_more_tokens(start, end)
        self.parser.pop_nodestack()
        self.parser.pop_handler()


ACTION_HANDLERS = {"switch": SwitchActionHandler}
