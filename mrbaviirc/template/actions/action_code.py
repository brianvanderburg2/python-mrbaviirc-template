""" Handler for the code action tag. """
# pylint: disable=too-few-public-methods, too-many-arguments, protected-access, unused-argument
# pylint: disable=exec-used

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node, NodeList
from ..tokenizer import Token
from ..errors import ParserError, TemplateError
from ..renderers import StringRenderer


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
            state.set_var(self.retvar, data)


class CodeSubHandler(ActionHandler):
    """ Handler for the code tag internals. """


    def handle_emitter(self, line, start, end):
        raise ParserError(
            self.template.filename,
            line,
            "No tags allowed in code section"
        )

    def handle_comment(self, line):
        raise ParserError(
            self.template.filename,
            line,
            "No tags allowed in code section"
        )

    def handle_break(self, line):
        raise ParserError(
            self.template.filename,
            line,
            "No tags allowed in code section"
        )

    def handle_continue(self, line):
        raise ParserError(
            self.template.filename,
            line,
            "No tags allowed in code section"
        )

    def handle_action_endcode(self, line, start, end):
        """ Handle end code. """
        self.parser._get_no_more_tokens(start, end)
        self.parser.pop_autostrip()
        self.parser.pop_nodestack()
        self.parser.pop_handler()


class CodeActionHandler(ActionHandler):
    """ Handler for code tag. """

    def handle_action_code(self, line, start, end):
        """ Handler for code tag. """
        parser = self.parser

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

        node = CodeNode(self.template, line, assigns, retvar)
        parser.add_node(node)
        parser.push_nodestack(node.nodes)
        parser.push_handler(CodeSubHandler(self.parser, self.template))
        parser.push_autostrip(parser.AUTOSTRIP_NONE)


ACTION_HANDLERS = {"code": CodeActionHandler}
