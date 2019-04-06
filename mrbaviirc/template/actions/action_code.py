""" Handler for the code action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import CodeNode
from ..tokenizer import Token
from ..errors import SyntaxError


def code_handler(parser, template, line, action, start, end):
    """ Parse the action """
    retvar = None
    assigns = []
    segments = parser._find_tag_segments(start, end)
    for segment in segments:
        (start, end) = segment

        token = parser._get_token(start, end)
        start += 1

        # expecting either return or with
        if token.type == Token.TYPE_WORD and token.value == "return":
            retvar = parser._get_token_var(start, end)
            start += 1

            parser._get_no_more_tokens(start, end)
            continue

        if token.type == Token.TYPE_WORD and token.value == "with":
            assigns = parser._parse_multi_assign(start, end)
            continue

        raise SyntaxError(
            "Unexpected token",
            template.filename,
            line
        )

    node = CodeNode(template, line, assigns, retvar)
    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(code_subhandler)
    parser.push_autostrip(parser.AUTOSTRIP_NONE)


def code_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """
    
    if action == "endcode":
        parser._get_no_more_tokens(start, end)
        parser.pop_nodestack()
        parser.pop_handler()
        parser.pop_autostrip()

    else:
        raise SyntaxError(
            "Nested tags not allowed in code",
            template.filename,
            line
        )


ACTION_HANDLERS = {"code": code_handler}
