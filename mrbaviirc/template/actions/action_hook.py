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

    def render(self, renderer, scope):
        """ Expand the variables. """

        hook = self.hook.eval(scope)
        params = {}
        for (name, expr) in self.assigns:
            params[name] = expr.eval(scope)

        scope.line = self.line
        self.env.call_hook(hook, renderer, scope, params, self.reverse)


def _hook_handler(parser, template, line, action, start, end, reverse):
    """ Parse the action. """
    hook = None
    assigns = []
    segments = parser._find_tag_segments(start, end)
    for segment in segments:
        (start, end) = segment

        token = parser._get_token(start, end)
        start += 1

        # expecting either with or expression
        if token.type == Token.TYPE_WORD and token.value == "with":
            assigns = parser._parse_multi_assign(start, end)
            continue

        # not with, then should be expression
        start -= 1
        hook = parser._parse_expr(start, end)

    if hook is None:
        raise ParserError(
            "Hook expecting name expression",
            template.filename,
            line)

    node = HookNode(template, line, hook, assigns, reverse)
    parser.add_node(node)


def hook_handler(parser, template, line, action, start, end):
    """ Parse the action """
    return _hook_handler(parser, template, line, action, start, end, False)


def rhook_handler(parser, template, line, action, start, end):
    """ Parse the action """
    return _hook_handler(parser, template, line, action, start, end, True)


ACTION_HANDLERS = {"hook": hook_handler, "rhook": rhook_handler}
