""" Handler for the for action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import ForNode
from ..tokenizer import Token
from ..errors import SyntaxError


def for_handler(parser, template, line, action, start, end):
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
    node = ForNode(template, line, var, cvar, expr)

    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(for_subhandler)


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
