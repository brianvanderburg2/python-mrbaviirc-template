""" Handler for the scope action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node, NodeList


class ScopeNode(Node):
    """ Create and remove scopes. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns
        self.nodes = NodeList()

    def render(self, renderer, scope):
        """ Render the scope. """
        new_scope = scope.push()

        for (var, expr) in self.assigns:
            new_scope.set(var, expr.eval(new_scope))

        self.nodes.render(renderer, new_scope)


def scope_handler(parser, template, line, action, start, end):
    """ Parse the action """
    if start <= end:
        assigns = parser._parse_multi_assign(start, end)
    else:
        assigns = []

    node = ScopeNode(template, line, assigns)
    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(scope_subhandler)

def scope_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """

    if action == "endscope":
        parser._get_no_more_tokens(start, end)
        parser.pop_nodestack()
        parser.pop_handler()

    else:
        parser.handle_action(parser, template, line, action, start, end)


ACTION_HANDLERS = {"scope": scope_handler}
