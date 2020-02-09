""" Handler for the include action tag. """
# pylint: disable=too-many-arguments, too-few-public-methods, protected-access, unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node
from ..tokenizer import Token
from ..errors import ParserError, TemplateError, RestrictedError


class IncludeNode(Node):
    """ A node to include another template. """

    def __init__(self, template, line, expr, assigns, retvar):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self.expr = expr
        self.assigns = assigns
        self.retvar = retvar

    def render(self, state):
        """ Actually do the work of including the template. """
        try:
            template = self.env.load_file(
                str(self.expr.eval(state)),
                self.template
            )
        except (IOError, OSError, RestrictedError) as error:
            raise TemplateError(
                str(error),
                self.template.filename,
                self.line
            )

        context = {}
        for (var, expr) in self.assigns:
            context[var] = expr.eval(state)

        retval = template.nested_render(state, context)
        if self.retvar:
            state.set_var(self.retvar[0], retval, self.retvar[1])


class IncludeActionHandler(ActionHandler):
    """ Handle the include action """

    def handle_action_include(self, line, start, end):
        """ Handle the include action """
        parser = self.parser

        expr = None
        retvar = None
        assigns = []
        segments = parser.find_tag_segments(start, end)

        # filename expr is first
        if len(segments) > 0:
            (start, end) = segments[0]
            expr = parser.parse_expr(start, end)

        for segment in segments[1:]:
            (start, end) = segment

            token = parser.get_expected_token(
                start,
                end,
                Token.TYPE_WORD,
                values=["return", "with"]
            )
            start += 1

            if token.value == "return":
                retvar = parser.get_token_var(start, end, allow_type=True)
                start += 1

                parser.get_no_more_tokens(start, end)
                continue

            if token.value == "with":
                assigns = parser.parse_multi_assign(start, end)
                continue

            # neither return or with, so expression
            start -= 1
            expr = parser.parse_expr(start, end)

        if expr is None:
            raise ParserError(
                "Include expecting path expression",
                self.template.filename,
                line
            )

        node = IncludeNode(self.template, line, expr, assigns, retvar)
        parser.add_node(node)


ACTION_HANDLERS = {"include": IncludeActionHandler}
