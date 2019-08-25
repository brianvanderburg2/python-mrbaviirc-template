""" Handler for the include action tag. """
# pylint: disable=too-many-arguments, too-few-public-methods, protected-access, unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node
from ..tokenizer import Token
from ..errors import ParserError, TemplateError, RestrictedError
from ..util import DictToAttr


class IncludeNode(Node):
    """ A node to include another template. """

    def __init__(self, template, line, expr, assigns, retvar):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self.expr = expr
        self.assigns = assigns
        self.retvar = retvar

    def render(self, renderer, scope):
        """ Actually do the work of including the template. """
        try:
            template = self.env.load_file(
                str(self.expr.eval(scope)),
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
            context[var] = expr.eval(scope)

        retval = template.nested_render(renderer, scope, context)
        if self.retvar:
            scope.set(self.retvar, DictToAttr(retval))


def include_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = None
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

        # neither return or with, so expression
        start -= 1
        expr = parser._parse_expr(start, end)

    if expr is None:
        raise ParserError(
            "Include expecting path expression",
            template.filename,
            line
        )

    node = IncludeNode(template, line, expr, assigns, retvar)
    parser.add_node(node)


ACTION_HANDLERS = {"include": include_handler}
