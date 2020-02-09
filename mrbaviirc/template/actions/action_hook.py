""" Handler for the hook and rhook action tags. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node
from ..tokenizer import Token
from ..errors import ParserError


class HookNode(Node):
    """ A node to call a registered hook. """

    def __init__(self, template, line, hook, assigns, reverse):
        """ Initialize """
        Node.__init__(self, template, line)
        self.hook = hook
        self.assigns = assigns
        self.reverse = reverse

    def render(self, state):
        """ Expand the variables. """

        hook = self.hook.eval(state)
        params = {}
        for (name, expr) in self.assigns:
            params[name] = expr.eval(state)

        state.line = self.line
        self.env.call_hook(hook, state, params, self.reverse)


class HookActionHandler(ActionHandler):
    """ Handle hook and rhook """

    def handle_action_hook(self, line, start, end):
        """ Handle hook """
        self._handle_action_hook(line, start, end, False)

    def handle_action_rhook(self, line, start, end):
        """ Handle rhook """
        self._handle_action_hook(line, start, end, True)

    def _handle_action_hook(self, line, start, end, reverse):
        """ Handle the actual parsing """
        hook = None
        assigns = []
        segments = self.parser.find_tag_segments(start, end)

        # First item should be expression
        if len(segments) > 0:
            (start, end) = segments[0]
            hook = self.parser.parse_expr(start, end)

        for segment in segments[1:]:
            (start, end) = segment

            # Only support "with"
            token = self.parser.get_expected_token(start, end, Token.TYPE_WORD, values="with")
            start += 1

            assigns = self.parser.parse_multi_assign(start, end)

        if hook is None:
            raise ParserError(
                "Hook expecting name expression",
                self.template.filename,
                line
            )

        node = HookNode(self.template, line, hook, assigns, reverse)
        self.parser.add_node(node)


ACTION_HANDLERS = {"hook": HookActionHandler, "rhook": HookActionHandler}
