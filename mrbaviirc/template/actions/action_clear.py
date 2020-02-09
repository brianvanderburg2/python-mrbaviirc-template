""" Handler for the clear action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node
from ..state import RenderState
from ..tokenizer import Token


class ClearNode(Node):
    """ Clear variables. """

    def __init__(self, template, line, where):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.where = where

    def render(self, state):
        """ Set the value. """
        state.clear_vars(self.where)


class ClearActionHandler(ActionHandler):
    """ Action handler for clear. """

    def handle_action_clear(self, line, start, end):
        """ Parse the action for clear """
        parser = self.parser
        where = RenderState.LOCAL_VAR

        if end >= start:
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

        node = ClearNode(self.template, line, where)
        parser.add_node(node)


ACTION_HANDLERS = {"clear": ClearActionHandler}
