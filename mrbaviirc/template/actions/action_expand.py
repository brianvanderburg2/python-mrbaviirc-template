""" Handler for the expand action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node
from ..errors import TemplateError
from ..state import RenderState
from ..tokenizer import Token


class ExpandNode(Node):
    """ A node to expand variables into the local variables. """

    def __init__(self, template, line, expr, where):
        """ Initialize """
        Node.__init__(self, template, line)
        self.expr = expr
        self.where = where

    def render(self, state):
        """ Expand the variables. """

        result = self.expr.eval(state)
        try:
            state.update_vars(result, self.where)
        except (KeyError, TypeError, ValueError) as error:
            raise TemplateError(
                str(error),
                self.template.filename,
                self.line
            )


class ExpandActionHandler(ActionHandler):
    """ Handle the expand action """

    def handle_action_expand(self, line, start, end):
        """ Handle the expand action """
        parser = self.parser
        segments = parser.find_tag_segments(start, end)

        expr = None
        where = RenderState.LOCAL_VAR

        # Expression is always first
        if len(segments) > 0:
            (start, end) = segments[0]
            expr = parser.parse_expr(start, end)

        for segment in segments[1:]:
            (start, end) = segment

            # Only support "into"
            parser.get_expected_token(start, end, Token.TYPE_WORD, values="into")
            start += 1

            # Get variable type
            token = parser.get_expected_token(
                start,
                end,
                Token.TYPE_WORD,
                values=["local", "global", "private", "return"]
            )
            start += 1

            where = {
                "local": RenderState.LOCAL_VAR,
                "global": RenderState.GLOBAL_VAR,
                "private": RenderState.PRIVATE_VAR,
                "return": RenderState.RETURN_VAR
            }.get(token.value, RenderState.LOCAL_VAR)

            parser.get_no_more_tokens(start, end)

        if expr is None:
            raise ParserError(
                "Expand expecting expression",
                self.template.filename,
                line
            )

        node = ExpandNode(self.template, line, expr, where)
        parser.add_node(node)


ACTION_HANDLERS = {"expand": ExpandActionHandler}
