""" Handler for the code action tag. """
# pylint: disable=too-few-public-methods, too-many-arguments, protected-access, unused-argument
# pylint: disable=exec-used

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node, NodeList
from ..tokenizer import Token
from ..errors import ParserError, TemplateError
from ..renderers import StringRenderer
from ..util import DictToAttr


class CodeNode(Node):
    """ A node to execute python code. """

    def __init__(self, template, line, assigns, retvar):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self.assigns = assigns
        self.retvar = retvar
        self.nodes = NodeList()
        self.code = None

    def render(self, state):
        """ Actually do the work of including the template. """

        # Must be allowed globally in env and also locally in template
        if not self.env.code_enabled or not self.template.code_enabled:
            raise TemplateError(
                "Use of direct python code not allowed",
                self.template.filename,
                self.line
            )

        # Compile the code only once
        # TODO: does this need lock for threading
        if not self.code:
            # Get the code
            try:
                original_renderer = state.renderer
                state.renderer = StringRenderer()
                self.nodes.render(state)
                code = state.renderer.get()
            finally:
                state.renderer = original_renderer

            # Compile it
            try:
                self.code = compile(code, "<string>", "exec")
            except Exception as error:
                raise TemplateError(
                    str(error),
                    self.template.filename,
                    self.line
                )

        # Execute the code
        data = {}
        for (var, expr) in self.assigns:
            data[var] = expr.eval(state)

        try:
            exec(self.code, data, data)
        except Exception as error:
            raise TemplateError(
                str(error),
                self.template.filename,
                self.line
            )

        # Handle return values
        if self.retvar:
            state.set_var(self.retvar, DictToAttr(data))


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

        raise ParserError(
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
        raise ParserError(
            "Nested tags not allowed in code",
            template.filename,
            line
        )


ACTION_HANDLERS = {"code": code_handler}
