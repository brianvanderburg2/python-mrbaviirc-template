""" Handler for the for action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import ForIterNode, ForIncrNode
from ..tokenizer import Token


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
