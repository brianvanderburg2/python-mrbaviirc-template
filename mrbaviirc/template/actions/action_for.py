""" Handler for the for action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node, NodeList
from ..tokenizer import Token


class ForIterNode(Node):
    """ A node for handling iteration for loops. """

    def __init__(self, template, line, var, cvar, expr):
        """ Initialize the for node. """
        Node.__init__(self, template, line)
        self.var = var
        self.cvar = cvar
        self.expr = expr

        self.for_nodes = NodeList()
        self.else_nodes = None
        self.nodes = self.for_nodes

    def add_else(self):
        """ Add an else section. """
        self.else_nodes = NodeList()
        self.nodes = self.else_nodes

    def render(self, renderer, scope):
        """ Render the for node. """
        # Iterate over each value
        values = self.expr.eval(scope)
        do_else = True
        if values:
            index = 0
            for var in values:
                do_else = False
                if self.cvar:
                    scope.set(self.cvar, index)
                scope.set(self.var, var)
                index += 1

                # Execute each sub-node
                result = self.for_nodes.render(renderer, scope)
                if result == Node.RENDER_BREAK:
                    break
                elif result == Node.RENDER_CONTINUE:
                    continue

        if do_else and self.else_nodes:
            return self.else_nodes.render(renderer, scope)


class ForIncrNode(Node):
    """ A node for handling increment for loops. """

    def __init__(self, template, line, init, test, incr):
        """ Initialize the for node. """
        Node.__init__(self, template, line)
        self.init = init
        self.test = test
        self.incr = incr

        self.for_nodes = NodeList()
        self.else_nodes = None
        self.nodes = self.for_nodes

    def add_else(self):
        """ Add an else section. """
        self.else_nodes = NodeList()
        self.nodes = self.else_nodes

    def render(self, renderer, scope):
        """ Render the for node. """
        # Init
        for (var, expr) in self.init:
            scope.set(var, expr.eval(scope))

        # Test
        do_else = True
        while bool(self.test.eval(scope)):
            do_else = False

            # Render nodes
            result = self.for_nodes.render(renderer, scope)
            if result == Node.RENDER_BREAK:
                break

            # Incr
            for (var, expr) in self.incr:
                scope.set(var, expr.eval(scope))

        if do_else and self.else_nodes:
            return self.else_nodes.render(renderer, scope)


def _for_iter_handler(parser, template, line, start, end):
    """ Parse the action """
    var = parser._get_token_var(start, end)
    start += 1

    token = parser._get_expected_token(
        start,
        end,
        [Token.TYPE_COMMA, Token.TYPE_WORD],
        "Expected 'in' or ','",
        "in"
    )
    start += 1

    cvar = None
    if token.type == Token.TYPE_COMMA:

        cvar = parser._get_token_var(start, end)
        start += 1

        token = parser._get_expected_token(
            start,
            end,
            Token.TYPE_WORD,
            "Expected 'in'",
            "in"
        )
        start += 1

    expr = parser._parse_expr(start, end)
    node = ForIterNode(template, line, var, cvar, expr)

    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(for_subhandler)


def _for_incr_handler(parser, template, line, segments):
    """ Parse the action """
    # Init
    (start, end) = segments[0]
    init = parser._parse_multi_assign(start, end)

    # Test
    (start, end) = segments[1]
    test = parser._parse_expr(start, end)

    # Incr
    (start, end) = segments[2]
    incr = parser._parse_multi_assign(start, end)

    node = ForIncrNode(template, line, init, test, incr)
    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(for_subhandler)



def for_handler(parser, template, line, action, start, end):
    """ Parse the action """

    # Two types of for
    # for var,var in expr (only one segment)
    # for init ; test ; incr (three segments)

    segments = parser._find_tag_segments(start, end)
    if len(segments) == 3:
        return _for_incr_handler(parser, template, line, segments)
    else:
        return _for_iter_handler(parser, template, line, start, end)


def for_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """

    if action == "else":
        parser._get_no_more_tokens(start, end)
        node = parser.pop_nodestack()
        node.add_else()
        parser.push_nodestack(node.nodes)

    elif action == "endfor":
        parser._get_no_more_tokens(start, end)
        parser.pop_nodestack()
        parser.pop_handler()

    else:
        parser.handle_action(parser, template, line, action, start, end)


ACTION_HANDLERS = {"for": for_handler}
