""" Handler for the hook and rhook action tags. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


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


def _hook_handler(parser, template, line, action, start, end, reverse):
    """ Parse the action. """
    hook = None
    assigns = []
    segments = parser._find_tag_segments(start, end)

    # First item should be expression
    if len(segments) > 0:
        (start, end) = segments[0]
        hook = parser._parse_expr(start, end)

    for segment in segments[1:]:
        (start, end) = segment

        # Only support "with"
        token = parser._get_expected_token(start, end, Token.TYPE_WORD, values="with")
        start += 1

        assigns = parser._parse_multi_assign(start, end)

    if hook is None:
        raise ParserError(
            "Hook expecting name expression",
            template.filename,
            line
        )

    node = HookNode(template, line, hook, assigns, reverse)
    parser.add_node(node)


def hook_handler(parser, template, line, action, start, end):
    """ Parse the action """
    return _hook_handler(parser, template, line, action, start, end, False)


def rhook_handler(parser, template, line, action, start, end):
    """ Parse the action """
    return _hook_handler(parser, template, line, action, start, end, True)


ACTION_HANDLERS = {"hook": hook_handler, "rhook": rhook_handler}
