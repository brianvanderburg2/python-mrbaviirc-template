""" Handler for the for action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler, DefaultActionHandler
from ..errors import ParserError
from ..nodes import Node, NodeList, BreakNode, ContinueNode
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

    def render(self, state):
        """ Render the for node. """
        # Iterate over each value
        values = self.expr.eval(state)
        do_else = True
        if values:
            index = 0
            for var in values:
                do_else = False
                if self.cvar:
                    state.set_var(self.cvar[0], index, self.cvar[1])
                state.set_var(self.var[0], var, self.var[1])
                index += 1

                # Execute each sub-node
                result = self.for_nodes.render(state)
                if result == Node.RENDER_BREAK:
                    break
                elif result == Node.RENDER_CONTINUE:
                    continue

        if do_else and self.else_nodes:
            return self.else_nodes.render(state)


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

    def render(self, state):
        """ Render the for node. """
        # Init
        for (var, expr) in self.init:
            state.set_var(var[0], expr.eval(state), var[1])

        # Test
        do_else = True
        while bool(self.test.eval(state)):
            do_else = False

            # Render nodes
            result = self.for_nodes.render(state)
            if result == Node.RENDER_BREAK:
                break

            # Incr
            for (var, expr) in self.incr:
                state.set_var(var[0], expr.eval(state), var[1])

        if do_else and self.else_nodes:
            return self.else_nodes.render(state)


class ForActionHandler(ActionHandler):
    """ Handle the for actions. """

    def handle_action_foreach(self, line, start, end):
        """ Parse the action for a for iterator """
        parser = self.parser
        var = parser.get_token_var(start, end, allow_type=True)
        start += 1

        token = parser.get_expected_token(
            start,
            end,
            [Token.TYPE_COMMA, Token.TYPE_WORD],
            "Expected 'in' or ','",
            "in"
        )
        start += 1

        cvar = None
        if token.type == Token.TYPE_COMMA:

            cvar = parser.get_token_var(start, end, allow_type=True)
            start += 1

            token = parser.get_expected_token(
                start,
                end,
                Token.TYPE_WORD,
                "Expected 'in'",
                "in"
            )
            start += 1

        expr = parser.parse_expr(start, end)
        node = ForIterNode(self.template, line, var, cvar, expr)

        parser.add_node(node)
        parser.push_nodestack(node.nodes)
        parser.push_handler(ForSubHandler(self.parser, self.template))

    def handle_action_for(self, line, start, end):
        """ Handle a for incrementer """
        parser = self.parser
        segments = parser.find_tag_segments(start, end)

        if len(segments) != 3:
            raise ParserError(
                self.template.filename,
                line,
                "Expecting init, test, and increment segments in for action"
            )

        # Init
        (start, end) = segments[0]
        init = parser.parse_multi_assign(start, end, allow_type=True)

        # Test
        (start, end) = segments[1]
        test = parser.parse_expr(start, end)

        # Incr
        (start, end) = segments[2]
        incr = parser.parse_multi_assign(start, end, allow_type=True)

        node = ForIncrNode(self.template, line, init, test, incr)
        parser.add_node(node)
        parser.push_nodestack(node.nodes)
        parser.push_handler(ForSubHandler(self.parser, self.template))


class ForSubHandler(DefaultActionHandler):
    """ Handle the tags inside for """

    def handle_action_endfor(self, line, start, end):
        """ End the for loop """
        self.parser.get_no_more_tokens(start, end)
        self.parser.pop_nodestack()
        self.parser.pop_handler()

    def handle_action_else(self, line, start, end):
        """ Handle if no items iterated over. """
        self.parser.get_no_more_tokens(start, end)
        node = self.parser.pop_nodestack()
        node.add_else()
        self.parser.push_nodestack(node.nodes)

    def handle_break(self, line):
        """ Allow break. """
        self.parser.add_node(BreakNode(self.template, line))

    def handle_continue(self, line):
        """ Allow continue. """
        self.parser.add_node(ContinueNode(self.template, line))


ACTION_HANDLERS = {"for": ForActionHandler, "foreach": ForActionHandler}
