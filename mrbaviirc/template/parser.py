""" A parser for the template engine. """
# pylint: disable=unused-wildcard-import,too-many-branches,too-many-statements
# pylint: disable=too-many-lines,too-few-public-methods,too-many-arguments
# pylint: disable=too-many-return-statements,too-many-instance-attributes

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


import re
import operator

from .errors import *
from .nodes import *
from .expr import *
from .scope import *
from .tokenizer import *


class TemplateParser(object):
    """ A base tokenizer. """

    AUTOSTRIP_NONE = 0
    AUTOSTRIP_STRIP = 1
    AUTOSTRIP_TRIM = 2

    OPEN_CLOSE_MAP = {
        Token.TYPE_OPEN_PAREN: Token.TYPE_CLOSE_PAREN,
        Token.TYPE_OPEN_BRACKET: Token.TYPE_CLOSE_BRACKET
    }

    CLOSE_TOKENS = [
        Token.TYPE_CLOSE_PAREN,
        Token.TYPE_CLOSE_BRACKET
    ]

    def __init__(self, template, text):
        """ Initialize the parser. """

        self.template = template
        self.text = text
        self.tokens = None

        # Stack and line number
        self._ops_stack = []
        self.nodes = NodeList()
        self.stack = [self.nodes]

        # Buffer for plain text segments
        self.buffer = []
        self.autostrip = self.AUTOSTRIP_NONE
        self.autostrip_stack = []

    def _get_token(self, pos, end, errmsg="Expected token"):
        """ Get a token at a position, raise error if not found/out of bound """

        if pos <= end:
            return self.tokens[pos]
        else:
            raise SyntaxError(
                errmsg,
                self.template.filename,
                self.tokens[pos - 1].line if pos > 0 else 0
            )


    def _get_expected_token(self, pos, end, types, errmsg="Unexpected token", values=None):
        """ Expect a specific type of token. """

        token = self._get_token(pos, end, errmsg)
        if not isinstance(types, (list, tuple)):
            types = [types]

        if token.type not in types:
            raise SyntaxError(
                errmsg,
                self.template.filename,
                token.line
            )

        if token.type == token.TYPE_WORD and values is not None:
            if not isinstance(values, (list, tuple)):
                values = [values]

            if token.value not in values:
                raise SyntaxError(
                    errmsg,
                    self.template.filename,
                    token.line
                )

        return token

    def _get_no_more_tokens(self, pos, end, errmsg="Unexpected token"):
        """ Expect the end of the range. """

        if pos <= end:
            raise SyntaxError(
                errmsg,
                self.template.filename,
                self.tokens[pos].line
            )

    def _get_token_var(self, pos, end, errmsg="Expected variable."):
        """ Parse a variable and return var """

        token = self._get_expected_token(pos, end, Token.TYPE_WORD, errmsg)
        if re.match("[a-zA-Z_][a-zA-Z0-9_]*", token.value):
            return token.value
        else:
            raise SyntaxError(
                "Invalid variable name: {0}".format(token.value),
                self.template.filename,
                token.line
            )

        # If we got here, it wasn't a variable
        raise SyntaxError(
            errmsg,
            self.template.filename,
            token.line
        )

    def _find_level0_token(self, start, end, token=None):
        """ Find a token at level 0 nesting. """

        token_stack = []
        first = None

        for pos in range(start, end + 1):
            newtoken = self.tokens[pos]

            if newtoken.type in self.OPEN_CLOSE_MAP:
                # Found an open token
                token_stack.append(newtoken.type)
                if len(token_stack) == 1:
                    first = pos

            elif newtoken.type in self.CLOSE_TOKENS:
                # Make sure it matches the
                if len(token_stack):
                    last = token_stack.pop()
                else:
                    last = None

                if last is None or newtoken.type != self.OPEN_CLOSE_MAP[last]:
                    raise SyntaxError(
                        "Mismatched or unclosed token",
                        self.template.filename,
                        newtoken.line
                    )

            elif len(token_stack) == 0:
                if token is None or token == newtoken.type:
                    return pos

        if token_stack:
            raise SyntaxError(
                "Unmatched braces/parenthesis",
                self.template.filename,
                self.tokens[first].line
            )

        return None

    def _find_level0_closing(self, start, end):
        """ Find the matching closing token. """

        token = self.tokens[start]
        if not token.type in self.OPEN_CLOSE_MAP:
            raise SyntaxError(
                "Unexpected token",
                self.template.filename,
                token.line
            )

        token_stack = [token.type]

        for pos in range(start + 1, end + 1):
            token = self.tokens[pos]

            if token.type in self.OPEN_CLOSE_MAP:
                token_stack.append(token.type)

            elif token.type in self.CLOSE_TOKENS:
                if len(token_stack):
                    last = token_stack.pop()
                else:
                    last = None

                if last is None or token.type != self.OPEN_CLOSE_MAP[last]:
                    raise SyntaxError(
                        "Mismatched or unclosed token",
                        self.template.filename,
                        token.line
                    )

                if len(token_stack) == 0:
                    # Popped of the start token, so this is the closing
                    return pos

        # If we get here, we never found the closing token
        raise SyntaxError(
            "Unmatched braces/parenthesis",
            self.template.filename,
            self.tokens[start].line
        )

    def _find_tag_segments(self, start, end):
        """ Return list of (start, end) for any tag segments. """

        result = []
        if end < start:
            return result

        while start <= end:
            pos = self._find_level0_token(start, end, Token.TYPE_SEMICOLON)
            if pos is None:
                break

            if pos == start or pos == end:
                raise SyntaxError(
                    "Unexpected semicolon",
                    self.template.filename,
                    self.tokens[pos].line # find_level0 doesn't use get_token
                )

            result.append((start, pos - 1))
            start = pos + 1

        # Anything left is last segment
        if start <= end:
            result.append((start, end))

        return result

    def parse(self):
        """ Parse the template and return the node list. """

        # Build our tokens
        tokenizer = Tokenizer(self.text, self.template.filename)
        self.tokens = tokenizer.parse()

        # Parse our body
        pre_ws_control = None
        pos = 0
        while pos < len(self.tokens):
            token = self.tokens[pos]

            if token.type == Token.TYPE_TEXT:
                self.buffer.append(token.value)
                pos += 1
                continue

            if token.type in (
                    Token.TYPE_START_COMMENT,
                    Token.TYPE_START_ACTION,
                    Token.TYPE_START_EMITTER
            ):
                # Flush the buffer
                self._flush_buffer(pre_ws_control, token.value)

                # Find the ending
                if token.type == Token.TYPE_START_COMMENT:
                    ending = Token.TYPE_END_COMMENT
                elif token.type == Token.TYPE_START_ACTION:
                    ending = Token.TYPE_END_ACTION
                elif token.type == Token.TYPE_START_EMITTER:
                    ending = Token.TYPE_END_EMITTER

                for endpos in range(pos + 1, len(self.tokens)):
                    if self.tokens[endpos].type == ending:
                        break
                else:
                    raise SyntaxError(
                        "Opening tag missing closing tag.",
                        self.template.filename,
                        token.line
                    )

                end_token = self.tokens[endpos]
                pre_ws_control = end_token.value

                # Parse the insides
                if token.type == Token.TYPE_START_ACTION:
                    self._parse_tag_action(pos + 1, endpos - 1)

                elif token.type == Token.TYPE_START_EMITTER:
                    self._parse_tag_emitter(pos + 1, endpos - 1)

                # comment is skipped entirely

                # Move past it
                pos = endpos + 1

        self._flush_buffer(pre_ws_control, None)

        if self._ops_stack:
            raise SyntaxError(
                "Unmatched action tag",
                self.template.filename,
                self._ops_stack[-1][1]
            )

        return self.nodes

    def _parse_tag_action(self, start, end):
        """ Parse some action tag. """

        # Determine the action
        token = self._get_token(start, end, "Expected action")
        action = token.value
        start += 1

        if action == "if":
            self._parse_action_if(start, end)
        elif action == "elif":
            self._parse_action_elif(start, end)
        elif action == "else":
            self._parse_action_else(start, end)
        elif action == "break":
            self._parse_action_break(start, end)
        elif action == "continue":
            self._parse_action_continue(start, end)
        elif action == "for":
            self._parse_action_for(start, end)
        elif action == "switch":
            self._parse_action_switch(start, end)
        elif action in SwitchNode.types:
            self._parse_action_switch_item(start, end, action)
        elif action == "set":
            self._parse_action_set(start, end, Scope.SCOPE_LOCAL)
        elif action == "global":
            self._parse_action_set(start, end, Scope.SCOPE_GLOBAL)
        elif action == "template":
            self._parse_action_set(start, end, Scope.SCOPE_TEMPLATE)
        elif action == "private":
            self._parse_action_set(start, end, Scope.SCOPE_PRIVATE)
        elif action == "unset":
            self._parse_action_unset(start, end)
        elif action == "scope":
            self._parse_action_scope(start, end)
        elif action == "code":
            self._parse_action_code(start, end)
        elif action == "include":
            self._parse_action_include(start, end)
        elif action == "return":
            self._parse_action_return(start, end)
        elif action == "expand":
            self._parse_action_expand(start, end)
        elif action == "section":
            self._parse_action_section(start, end)
        elif action == "use":
            self._parse_action_use(start, end)
        elif action == "var":
            self._parse_action_var(start, end)
        elif action == "error":
            self._parse_action_error(start, end)
        elif action == "import":
            self._parse_action_import(start, end)
        elif action == "do":
            self._parse_action_do(start, end)
        elif action.startswith("end"):
            self._parse_action_end(start, end, action)
        elif action == "strip":
            self._parse_action_strip(start, end)
        elif action == "autostrip":
            self.autostrip = self.AUTOSTRIP_STRIP
        elif action == "autotrim":
            self.autostrip = self.AUTOSTRIP_TRIM
        elif action == "no_autostrip":
            self.autostrip = self.AUTOSTRIP_NONE
        else:
            raise SyntaxError(
                "Unknown action tag: {0}".format(action),
                self.template.filename,
                token.line
            )

    def _parse_action_if(self, start, end):
        """ Parse an if action. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        node = IfNode(self.template, line, expr)

        self._ops_stack.append(("if", line))
        self.stack[-1].append(node)
        self.stack.append(node.nodes)

    def _parse_action_elif(self, start, end):
        """ Parse an elif action. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        if not self._ops_stack:
            raise SyntaxError(
                "Mismatched elif",
                self.template.filename,
                line
            )

        what = self._ops_stack[-1]
        if what[0] != "if":
            raise SyntaxError(
                "Mismatched elif",
                self.template.filename,
                line
            )

        self.stack.pop()
        node = self.stack[-1][-1]
        node.add_elif(expr)
        self.stack.append(node.nodes)

    def _parse_action_else(self, start, end):
        """ Parse an else. """

        self._get_no_more_tokens(start, end)
        line = self.tokens[start - 1].line if start > 0 else 0

        if not self._ops_stack:
            raise SyntaxError(
                "Mismatched else",
                self.template.filename,
                line
            )

        what = self._ops_stack[-1]
        if not what[0] in ("if", "for"):
            raise SyntaxError(
                "Mismatched else",
                self.template.filename,
                line
            )

        # Both if and for do this the same way
        self.stack.pop()
        node = self.stack[-1][-1]
        node.add_else()
        self.stack.append(node.nodes)

    def _parse_action_break(self, start, end):
        """ Parse break. """

        self._get_no_more_tokens(start, end)
        line = self.tokens[start - 1].line if start > 0 else 0

        node = BreakNode(self.template, line)
        self.stack[-1].append(node)

    def _parse_action_continue(self, start, end):
        """ Parse continue. """

        self._get_no_more_tokens(start, end)
        line = self.tokens[start - 1].line if start > 0 else 0

        node = ContinueNode(self.template, line)
        self.stack[-1].append(node)

        return start

    def _parse_action_for(self, start, end):
        """ Parse a for statement. """
        # TODO: with new segments, support for <a>[,<b>] in expr and also
        # for init ; test ; step (init and step are multi-assign, test is expr)
        # Or, simplification, change for to foreach, both can still have else
        # foreach if there are no results, for if first test is false/no iterations
        # and break to break out of loop

        var = self._get_token_var(start, end)
        line = self.tokens[start].line
        start += 1

        token = self._get_expected_token(
            start,
            end,
            [Token.TYPE_COMMA, Token.TYPE_WORD],
            "Expected 'in' or ','",
            "in"
        )
        start += 1

        cvar = None
        if token.type == Token.TYPE_COMMA:

            cvar = self._get_token_var(start, end)
            start += 1

            token = self._get_expected_token(
                start,
                end,
                Token.TYPE_WORD,
                "Expected 'in'",
                "in"
            )
            start += 1

        expr = self._parse_expr(start, end)

        node = ForNode(self.template, line, var, cvar, expr)
        self._ops_stack.append(("for", line))
        self.stack[-1].append(node)
        self.stack.append(node.nodes)

    def _parse_action_switch(self, start, end):
        """ Parse a switch statement. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        node = SwitchNode(self.template, line, expr)
        self._ops_stack.append(("switch", line))
        self.stack[-1].append(node)
        self.stack.append(node.nodes)

    def _parse_action_switch_item(self, start, end, item):
        """ Parse the switch item. """
        line = self.tokens[start - 1].line if start > 0 else 0

        if not self._ops_stack:
            raise SyntaxError(
                "{0} can only occur in switch".format(item),
                self.template.filename,
                line
            )

        what = self._ops_stack[-1]
        if what[0] != "switch":
            raise SyntaxError(
                "{0} can only occur in switch".format(item),
                self.template.filename,
                line
            )

        offset = SwitchNode.types.index(item)
        argc = SwitchNode.argc[offset]

        exprs = self._parse_multi_expr(start, end)

        if len(exprs) != argc:
            raise SyntaxError(
                "Switch clause {0} takes {1} argument".format(item, argc),
                self.template.filename,
                line
            )

        self.stack.pop()
        node = self.stack[-1][-1]
        node.add_case(SwitchNode.cbs[offset], exprs)
        self.stack.append(node.nodes)

    def _parse_action_set(self, start, end, where):
        """ Parse a set statement. """
        assigns = self._parse_multi_assign(start, end)
        line = self.tokens[start].line

        node = AssignNode(self.template, line, assigns, where)
        self.stack[-1].append(node)

    def _parse_action_unset(self, start, end):
        """ Parse an unset statement. """
        varlist = self._parse_multi_var(start, end)
        line = self.tokens[start].line

        node = UnsetNode(self.template, line, varlist)
        self.stack[-1].append(node)

    def _parse_action_scope(self, start, end):
        """ Parse a scope statement. """
        line = self.tokens[start - 1].line if start > 0 else 0
        if start <= end:
            assigns = self._parse_multi_assign(start, end)
        else:
            assigns = []

        node = ScopeNode(self.template, line, assigns)
        self._ops_stack.append(("scope", line))
        self.stack[-1].append(node)
        self.stack.append(node.nodes)

    def _parse_action_code(self, start, end):
        """ Parse a code node. """
        line = self.tokens[start - 1].line if start > 0 else 0

        # disable autostrip for this block
        self.autostrip_stack.append(self.autostrip)
        self.autostrip = self.AUTOSTRIP_NONE

        retvar = None
        assigns = []
        segments = self._find_tag_segments(start, end)
        for segment in segments:
            (start, end) = segment

            token = self._get_token(start, end)
            start += 1

            # expecting either return or with
            if token.type == Token.TYPE_WORD and token.value == "return":
                retvar = self._get_token_var(start, end)
                start += 1

                self._get_no_more_tokens(start, end)
                continue

            if token.type == Token.TYPE_WORD and token.value == "with":
                assigns = self._parse_multi_assign(start, end)
                continue

            raise SyntaxError(
                "Unexpected token",
                self.template.filename,
                self.tokens[start].line
            )


        self._ops_stack.append(("code", line))
        node = CodeNode(self.template, line, assigns, retvar)
        self.stack[-1].append(node)
        self.stack.append(node.nodes)

    def _parse_action_include(self, start, end):
        """ Parse an include node. """
        line = self.tokens[start - 1].line if start > 0 else start

        retvar = None
        assigns = []
        segments = self._find_tag_segments(start, end)
        for segment in segments:
            (start, end) = segment

            token = self._get_token(start, end)
            start += 1

            # expecting either return or with
            if token.type == Token.TYPE_WORD and token.value == "return":
                retvar = self._get_token_var(start, end)
                start += 1

                self._get_no_more_tokens(start, end)
                continue

            if token.type == Token.TYPE_WORD and token.value == "with":
                assigns = self._parse_multi_assign(start, end)
                continue

            # neither return or with, so expression
            start -= 1
            expr = self._parse_expr(start, end)


        node = IncludeNode(self.template, line, expr, assigns, retvar)
        self.stack[-1].append(node)

    def _parse_action_return(self, start, end):
        """ Parse a return variable node. """
        assigns = self._parse_multi_assign(start, end)
        line = self.tokens[start].line

        node = ReturnNode(self.template, line, assigns)
        self.stack[-1].append(node)

    def _parse_action_expand(self, start, end):
        """ Parse an expand node. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        node = ExpandNode(self.template, line, expr)
        self.stack[-1].append(node)

    def _parse_action_section(self, start, end):
        """ Parse a section node. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        self._ops_stack.append(("section", line))
        node = SectionNode(self.template, line, expr)
        self.stack[-1].append(node)
        self.stack.append(node.nodes)

    def _parse_action_use(self, start, end):
        """ Parse a use section node. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        node = UseSectionNode(self.template, line, expr)
        self.stack[-1].append(node)

    def _parse_action_var(self, start, end):
        """ Parse a block to store rendered output in a variable. """
        var = self._get_token_var(start, end)
        line = self.tokens[start].line
        start += 1

        self._get_no_more_tokens(start, end)

        node = VarNode(self.template, line, var)
        self._ops_stack.append(("var", line))
        self.stack[-1].append(node)
        self.stack.append(node.nodes)

    def _parse_action_error(self, start, end):
        """ Raise an error from the template. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        node = ErrorNode(self.template, line, expr)
        self.stack[-1].append(node)

    def _parse_action_import(self, start, end):
        """ Parse an import action. """
        assigns = self._parse_multi_assign(start, end)
        line = self.tokens[start].line

        node = ImportNode(self.template, line, assigns)
        self.stack[-1].append(node)

    def _parse_action_do(self, start, end):
        """ Parse a do tag. """
        nodes = self._parse_multi_expr(start, end)
        line = self.tokens[start].line

        node = DoNode(self.template, line, nodes)
        self.stack[-1].append(node)

    def _parse_action_end(self, start, end, action):
        """ Parse an end tag """
        self._get_no_more_tokens(start, end)
        line = self.tokens[start - 1].line if start > 0 else 0

        if not self._ops_stack:
            raise SyntaxError(
                "To many ends: {0}".format(action),
                self.template.filename,
                line
            )
        elif start <= end:
            raise SyntaxError(
                "Unexpected token",
                self.template.filename,
                self.tokens[start].line
            )

        what = self._ops_stack[-1]
        if what[0] != action[3:]:
            raise SyntaxError(
                "Mismatched end tag: {0}".format(action),
                self.template.filename,
                line
            )

        self._ops_stack.pop()

        # Handle certain tags

        # Pop node stack for any op that created a new node stack
        if not what[0] == "strip":
            self.stack.pop()

        # Restore autostrip value for any op that pushed the value
        if what[0] in ("strip", "code"):
            self.autostrip = self.autostrip_stack.pop()

    def _parse_action_strip(self, start, end):
        """ Change the autostrip state. """
        line = self.tokens[start - 1].line if start > 0 else 0

        self.autostrip_stack.append(self.autostrip)
        self._ops_stack.append(("strip", line))

        if start <= end:
            token = self._get_expected_token(
                start,
                end,
                Token.TYPE_WORD,
                "Expected on, off, or trim",
                ["on", "off", "trim"]
            )
            start += 1
        else:
            # No change
            return

        if token.value == "on":
            self.autostrip = self.AUTOSTRIP_STRIP
        elif token.value == "trim":
            self.autostrip = self.AUTOSTRIP_TRIM
        else:
            self.autostrip = self.AUTOSTRIP_NONE

    def _parse_tag_emitter(self, start, end):
        """ Parse an emitter tag. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        if isinstance(expr, ValueExpr):
            node = TextNode(self.template, line, str(expr.eval(None)))
        else:
            node = EmitNode(self.template, line, expr)
        self.stack[-1].append(node)

    def _parse_expr(self, start, end):
        """ Parse the expression. """

        addsub = None
        muldivmod = None
        posneg = None
        andor = None
        nott = None
        compare = None

        pos = start
        while pos <= end:
            # Find the token
            pos = self._find_level0_token(pos, end)
            if pos is None:
                break

            token = self.tokens[pos]

            # Keep track of certain types
            # We ignore many dependency how we split

            if token.type == Token.TYPE_SEMICOLON:
                raise SyntaxError(
                    "Unexpected semicolon",
                    self.template.filename,
                    token.line
                )

            if token.type in (
                    Token.TYPE_MULTIPLY, Token.TYPE_DIVIDE,
                    Token.TYPE_FLOORDIV, Token.TYPE_MODULUS
            ):
                muldivmod = pos
                pos += 1
                continue

            if token.type in (Token.TYPE_PLUS, Token.TYPE_MINUS):
                if pos == start:
                    # At start, it is a positive or negative
                    if posneg is None:
                        posneg = pos
                else:
                    lasttoken = self.tokens[pos - 1]
                    if lasttoken.type in (
                            Token.TYPE_ASSIGN, Token.TYPE_PLUS, Token.TYPE_MINUS,
                            Token.TYPE_MULTIPLY, Token.TYPE_DIVIDE,
                            Token.TYPE_FLOORDIV, Token.TYPE_MODULUS,
                            Token.TYPE_EQUAL, Token.TYPE_NOT_EQUAL,
                            Token.TYPE_GREATER, Token.TYPE_GREATER_EQUAL,
                            Token.TYPE_LESS, Token.TYPE_LESS_EQUAL,
                            Token.TYPE_NOT
                    ):
                        # After any of those, it is positive or negative
                        if posneg is None:
                            posneg = pos
                    else:
                        # Else, it is addition and subtraction
                        # Keep track of last one for correct order
                        addsub = pos
                pos += 1
                continue

            if token.type in (
                    Token.TYPE_EQUAL, Token.TYPE_NOT_EQUAL,
                    Token.TYPE_GREATER, Token.TYPE_GREATER_EQUAL,
                    Token.TYPE_LESS, Token.TYPE_LESS_EQUAL
            ):
                compare = pos
                pos += 1
                continue

            if token.type in (Token.TYPE_AND, Token.TYPE_OR):
                andor = pos
                pos += 1
                continue

            if token.type == Token.TYPE_NOT:
                nott = pos
                pos += 1
                continue

            # Unrecognized token is okay here
            pos += 1
            continue


        # Now we handle things based on what we found

        # Split on and/or first
        if andor is not None:
            token = self.tokens[andor]
            expr1 = self._parse_expr(start, andor - 1)
            expr2 = self._parse_expr(andor + 1, end)

            if token.type == Token.TYPE_AND:
                oper = lambda a, b: a and b
            else:
                oper = lambda a, b: a or b

            return BooleanBinaryExpr(
                self.template.filename,
                token.line,
                oper,
                expr1,
                expr2
            )

        # Split on comparison next
        if compare is not None:
            token = self.tokens[compare]
            expr1 = self._parse_expr(start, compare - 1)
            expr2 = self._parse_expr(compare + 1, end)

            if token.type == Token.TYPE_EQUAL:
                oper = operator.eq
            elif token.type == Token.TYPE_NOT_EQUAL:
                oper = operator.ne
            elif token.type == Token.TYPE_GREATER:
                oper = operator.gt
            elif token.type == Token.TYPE_GREATER_EQUAL:
                oper = operator.ge
            elif token.type == Token.TYPE_LESS:
                oper = operator.lt
            elif token.type == Token.TYPE_LESS_EQUAL:
                oper = operator.le

            return BooleanBinaryExpr(
                self.template.filename,
                token.line,
                oper,
                expr1,
                expr2
            )

        # Add/sub next
        if addsub is not None:
            token = self.tokens[addsub]
            expr1 = self._parse_expr(start, addsub - 1)
            expr2 = self._parse_expr(addsub + 1, end)

            if token.type == Token.TYPE_PLUS:
                oper = operator.add
            else:
                oper = operator.sub

            return BinaryExpr(
                self.template.filename,
                token.line,
                oper,
                expr1,
                expr2
            )

        # Mul/div/mod next
        if muldivmod is not None:
            token = self.tokens[muldivmod]
            expr1 = self._parse_expr(start, muldivmod - 1)
            expr2 = self._parse_expr(muldivmod + 1, end)

            if token.type == Token.TYPE_MULTIPLY:
                oper = operator.mul
            elif token.type == Token.TYPE_DIVIDE:
                oper = operator.truediv
            elif token.type == Token.TYPE_FLOORDIV:
                oper = operator.floordiv
            else:
                oper = operator.mod

            return BinaryExpr(
                self.template.filename,
                token.line,
                oper,
                expr1,
                expr2
            )

        # At this point, no more binary operators

        # Not
        if nott is not None:
            token = self.tokens[nott]
            if nott == start:
                return BooleanUnaryExpr(
                    self.template.filename,
                    token.line,
                    lambda a: not a,
                    self._parse_expr(nott + 1, end)
                )
            else:
                raise SyntaxError(
                    "Unexpected token: !",
                    self.template.filename,
                    token.line
                )

        # Posneg
        if posneg is not None:
            token = self.tokens[posneg]
            if posneg == start:
                if token.type == Token.TYPE_PLUS:
                    return self._parse_expr(posneg + 1, end)
                else:
                    return UnaryExpr(
                        self.template.filename,
                        token.line,
                        lambda a: -a,
                        self._parse_expr(posneg + 1, end)
                    )
            else:
                raise SyntaxError(
                    "Unexpected token: {0}".format(
                        "+" if token.type == Token.TYPE_PLUS else "-"
                    ),
                    self.template.filename,
                    token.line
                )

        # Check what we have at the start
        token = self.tokens[start]

        if token.type == Token.TYPE_OPEN_PAREN:
            # Find closing paren, treat all as expression
            closing = self._find_level0_closing(start, end)
            expr = self._parse_expr(start + 1, closing - 1)

            if closing < end:
                expr = self._parse_continuation(expr, closing + 1, end)

            return expr

        if token.type == Token.TYPE_OPEN_BRACKET:
            # Find closing bracket
            closing = self._find_level0_closing(start, end)
            expr = self._parse_expr_list(start + 1, closing - 1)

            if closing < end:
                expr = self._parse_continuation(expr, closing + 1, end)

            return expr

        if token.type == Token.TYPE_WORD:
            # Variable
            var = self._get_token_var(start, end)
            expr = VarExpr(self.template, token.line, var)

            if start < end:
                expr = self._parse_continuation(expr, start + 1, end)

            return expr

        if token.type in (Token.TYPE_STRING, Token.TYPE_INTEGER, Token.TYPE_FLOAT):
            expr = ValueExpr(self.template, token.line, token.value)

            if start < end:
                expr = self._parse_continuation(expr, start + 1, end)

            return expr

        raise SyntaxError(
            "Unexpected token",
            self.template.filename,
            token.line
        )

    def _parse_continuation(self, expr, start, end):
        """ Parse a continuation of an expression. """

        while start <= end:
            token = self.tokens[start]

            if token.type == Token.TYPE_DOT:
                start += 1
                if start <= end:
                    var = self._get_token_var(start, end)
                    expr = LookupAttrExpr(self.template, token.line, expr, var)
                    start += 1
                    continue

                raise SyntaxError(
                    "Expected variable name",
                    self.template.filename,
                    token.line
                )

            if token.type == Token.TYPE_OPEN_PAREN:
                closing = self._find_level0_closing(start, end)
                if start < closing - 1:
                    exprs = self._parse_multi_expr(start + 1, closing - 1)
                else:
                    exprs = []
                expr = FuncExpr(self.template, token.line, expr, exprs)
                start = closing + 1
                continue

            if token.type == Token.TYPE_OPEN_BRACKET:
                closing = self._find_level0_closing(start, end)
                expr1 = self._parse_expr(start + 1, closing - 1)
                expr = LookupItemExpr(self.template, token.line, expr, expr1)
                start = closing + 1
                continue

            raise SyntaxError(
                "Unexpected token",
                self.template.filename,
                token.line
                )

        return expr

    def _parse_expr_list(self, start, end):
        """ Pare an expression that's a list. """
        line = self.tokens[start - 1].line if start > 0 else 0
        if start <= end:
            nodes = self._parse_multi_expr(start, end)
        else:
            nodes = []

        if nodes and all(isinstance(node, ValueExpr) for node in nodes):
            node = ValueExpr(self.template, nodes[0].line, [node.eval(None) for node in nodes])
        else:
            node = ListExpr(self.template, line, nodes)
        return node

    def _parse_multi_expr(self, start, end):
        """ Parse a list of expressions separated by comma. """
        items = []

        if start <= end:
            pos = start
            while pos <= end:
                commapos = self._find_level0_token(pos, end, Token.TYPE_COMMA)
                if commapos is not None:
                    items.append(self._parse_expr(pos, commapos - 1))
                    pos = commapos + 1
                else:
                    items.append(self._parse_expr(pos, end))
                    pos = end + 1

            return items
        else:
            raise SyntaxError(
                "Expected expression list",
                self.template.filename,
                self.tokens[start - 1] if start > 0 else 0
            )

    def _parse_assign(self, start, end):
        """ Parse a var = expr assignment, return (var, expr, pos) """
        var = self._get_token_var(start, end)
        start += 1

        token = self._get_expected_token(start, end, Token.TYPE_ASSIGN, "Expected '='")
        start += 1

        expr = self._parse_expr(start, end)

        return (var, expr)

    def _parse_multi_assign(self, start, end):
        """ Parse multiple var = expr statemetns, return [(var, expr)] """
        assigns = []

        if start <= end:
            pos = start
            while pos <= end:
                commapos = self._find_level0_token(pos, end, Token.TYPE_COMMA)
                if commapos is not None:
                    assigns.append(self._parse_assign(pos, commapos - 1))
                    pos = commapos + 1
                else:
                    assigns.append(self._parse_assign(pos, end))
                    pos = end + 1

            return assigns
        else:
            raise SyntaxError(
                "Expected assignment list.",
                self.template.filename,
                self.tokens[start - 1].line if start > 0 else 0
            )

    def _parse_multi_var(self, start, end):
        """ Parse multiple variables and return (varlist, pos)
            Note: Return pos points at ending token.
        """

        if start <= end:
            varlist = []
            while start <= end:
                varlist.append(self._get_token_var(start, end))
                start += 1

                if start <= end:
                    # More left, should have a comma
                    self._get_expected_token(start, end, Token.TYPE_COMMA)
                    start += 1

            return varlist
        else:
            raise SyntaxError(
                "Expected variable list",
                self.template.filename,
                self.tokens[start - 1].line if start > 0 else 0
            )

    def _flush_buffer(self, pre_ws_control, post_ws_control):
        """ Flush the buffer to output. """
        text = ""
        if self.buffer:
            text = "".join(self.buffer)

            if self.autostrip == self.AUTOSTRIP_STRIP:
                text = text.strip()
            elif self.autostrip == self.AUTOSTRIP_TRIM:
                tmp = []
                need_nl = False
                for line in text.splitlines():
                    line = line.strip()
                    if line:
                        if need_nl:
                            tmp.append("\n")
                        tmp.append(line)
                        need_nl = True
                text = "".join(tmp)
            else:
                if pre_ws_control in (Token.WS_TRIMTONL, Token.WS_TRIMTONL_PRESERVENL):
                    # If the previous tag had a white-space control {{ ... -}}
                    # trim the start of this buffer up to/including a new line
                    # If the previous tag has a white-space control {{^ .. }}
                    # trim the start of the buffer up to but excluding a new line
                    first_nl = text.find("\n")
                    if first_nl == -1:
                        text = text.lstrip()
                    else:
                        nl = 1 if pre_ws_control == Token.WS_TRIMTONL else 0
                        text = text[:first_nl + nl].lstrip() + text[first_nl + nl:]

                if post_ws_control in (Token.WS_TRIMTONL, Token.WS_TRIMTONL_PRESERVENL):
                    # If the current tag has a white-space control {{- ... }}
                    # trim the end of the buffer up to/including a new line
                    # If the current tag has a white-space control {{^ .. }}
                    # trim the end of the buffer up to but excluding a new line
                    last_nl = text.rfind("\n")
                    if last_nl == -1:
                        text = text.rstrip()
                    else:
                        nl = 0 if post_ws_control == Token.WS_TRIMTONL else 1
                        text = text[:last_nl + nl] + text[last_nl + nl:].rstrip()

        if pre_ws_control == Token.WS_ADDNL:
            text = "\n" + text
        elif pre_ws_control == Token.WS_ADDSP:
            text = " " + text

        if post_ws_control == Token.WS_ADDNL:
            text = text + "\n"
        elif post_ws_control == Token.WS_ADDSP:
            text = text + " "

        if text:
            # Use line 0 b/c we don't report errors on TextNodes
            # Other solution would be to append the text tokens instead of
            # values, then have access to the line
            node = TextNode(self.template, 0, text)
            self.stack[-1].append(node)

        self.buffer = []
