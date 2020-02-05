""" A parser for the template engine. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


import re
import operator

from .errors import * # pylint: disable=wildcard-import
from .nodes import * # pylint: disable=wildcard-import
from .expr import * # pylint: disable=wildcard-import
from .state import RenderState
from .tokenizer import * # pylint: disable=wildcard-import
from .actions import ACTION_HANDLERS


class TemplateParser:
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
        self.nodes = NodeList()
        self.stack = [self.nodes]

        # Buffer for plain text segments
        self.buffer = []
        self.autostrip = self.AUTOSTRIP_NONE
        self.autostrip_stack = []

        # Handlers
        self.action_line = 0
        self.action_handlers = ACTION_HANDLERS
        self.action_handler_stack = [(0, self.handle_action)] # tuple of (line, handler)

    def push_handler(self, handler):
        """ Push a handler onto the handler stack. """
        self.action_handler_stack.append((self.action_line, handler))

    def pop_handler(self):
        """ Pop a handler off the stack. """

        if len(self.action_handler_stack) > 1:
            self.action_handler_stack.pop()
        else:
            raise ParserError(
                "Unexpected handler pop",
                self.template.filename,
                self.action_line
            )

    def handle_action(self, parser, template, line, action, start, end):
        """ Handle the main actions. """
        assert self is parser

        handler = self.action_handlers.get(action, None)
        if handler:
            handler(parser, template, line, action, start, end)
        else:
            raise ParserError(
                "Unknown action: {0}".format(action),
                template.filename,
                line
            )

    def add_node(self, node):
        """ Add a node to the current nodelist. """
        self.stack[-1].append(node)

    def push_nodestack(self, nodelist):
        """ Push a new nodelist as the current nodelist. """
        self.stack.append(nodelist)

    def pop_nodestack(self):
        """ Pop the nodelist and return the last node of the previous nodelist. """
        if len(self.stack) > 1:
            self.stack.pop()
            return self.stack[-1][-1]

        raise ParserError(
            "Unexpected nodelist pop",
            self.template.filename,
            self.action_line
        )

    def push_autostrip(self, value=None):
        """ Push autostrip and optionally change the value. """
        self.autostrip_stack.append(self.autostrip)
        if value is not None:
            self.autostrip = value

    def pop_autostrip(self):
        """ Pop autostrip value. """
        if len(self.autostrip_stack) > 0:
            self.autostrip = self.autostrip_stack.pop()
        else:
            raise ParserError(
                "Unexpected autostrip pop",
                self.template.filename,
                self.action_line
            )

    def set_autostrip(self, value):
        """ Set the autostrip value. """
        self.autostrip = value

    def _get_token(self, pos, end, errmsg="Expected token"):
        """ Get a token at a position, raise error if not found/out of bound """

        if pos <= end:
            return self.tokens[pos]

        raise ParserError(
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
            raise ParserError(
                errmsg,
                self.template.filename,
                token.line
            )

        if token.type == token.TYPE_WORD and values is not None:
            if not isinstance(values, (list, tuple)):
                values = [values]

            if token.value not in values:
                raise ParserError(
                    errmsg,
                    self.template.filename,
                    token.line
                )

        return token

    def _get_no_more_tokens(self, pos, end, errmsg="Unexpected token"):
        """ Expect the end of the range. """

        if pos <= end:
            raise ParserError(
                errmsg,
                self.template.filename,
                self.tokens[pos].line
            )

    def _get_token_var(self, pos, end, allow_type=False, errmsg="Expected variable."):
        """ Parse a variable and return var """

        token = self._get_expected_token(pos, end, Token.TYPE_WORD, errmsg)
        match = re.match("([lgpra]@)?([a-zA-Z_][a-zA-Z0-9_]*)", token.value)

        if match:
            var_type = match.group(1) # May be None if type not directly specified
            var_name = match.group(2)

            if allow_type:
                if var_type == "l@":
                    return (var_name, RenderState.LOCAL_VAR)
                if var_type == "g@":
                    return (var_name, RenderState.GLOBAL_VAR)
                if var_type == "p@":
                    return (var_name, RenderState.PRIVATE_VAR)
                if var_type == "r@":
                    return (var_name, RenderState.RETURN_VAR)
                if var_type == "a@":
                    return (var_name, RenderState.APP_VAR)
                if var_type is None:
                    # Guess type from variable name
                    # _=private, _.*_ = global, _.*[^_]=private, others=local
                    if var_name[0] == "_":
                        if len(var_name) == 1 or var_name[-1] != "_":
                            return (var_name, RenderState.PRIVATE_VAR)

                        return (var_name, RenderState.GLOBAL_VAR)

                    return (var_name, RenderState.LOCAL_VAR)
            elif var_type is None: # If allow_type is False, var_type should not be specified
                return var_name

        # no match, invalid type, or type specified when allow_type False
        raise ParserError(
            "Invalid variable name: {0}".format(token.value),
            self.template.filename,
            token.line
        )

    def _find_level0_token(self, start, end, tokens=None):
        """ Find a token at level 0 nesting. """

        token_stack = []
        first = None

        if tokens is not None and not isinstance(tokens, (list, tuple)):
            tokens = [tokens]

        for pos in range(start, end + 1):
            newtoken = self.tokens[pos]

            if newtoken.type in self.OPEN_CLOSE_MAP:
                # Found an open token
                token_stack.append(newtoken.type)
                if len(token_stack) == 1:
                    first = pos

            elif newtoken.type in self.CLOSE_TOKENS:
                # Make sure it matches the
                if token_stack:
                    last = token_stack.pop()
                else:
                    last = None

                if last is None or newtoken.type != self.OPEN_CLOSE_MAP[last]:
                    raise ParserError(
                        "Mismatched or unclosed token",
                        self.template.filename,
                        newtoken.line
                    )

            elif len(token_stack) == 0:
                if tokens is None or newtoken.type in tokens:
                    return pos

        if token_stack:
            raise ParserError(
                "Unmatched braces/parenthesis",
                self.template.filename,
                self.tokens[first].line
            )

        return None

    def _find_level0_closing(self, start, end):
        """ Find the matching closing token. """

        token = self.tokens[start]
        if not token.type in self.OPEN_CLOSE_MAP:
            raise ParserError(
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
                if token_stack:
                    last = token_stack.pop()
                else:
                    last = None

                if last is None or token.type != self.OPEN_CLOSE_MAP[last]:
                    raise ParserError(
                        "Mismatched or unclosed token",
                        self.template.filename,
                        token.line
                    )

                if len(token_stack) == 0:
                    # Popped of the start token, so this is the closing
                    return pos

        # If we get here, we never found the closing token
        raise ParserError(
            "Unmatched braces/parenthesis",
            self.template.filename,
            self.tokens[start].line
        )

    def _split_tokens(self, start, end, sep, allow_blank=False, errmsg="Expected Token"):
        """ Split a stream of tokens by another token.
            If allow_blank is True, allow for blank items in the result
            (if the seperator token is at the start, end, or back to back) """

        # Check for empty token set if allowed
        if start > end:
            return []

        # First find all ranges before any separators
        result = []
        while start <= end:
            pos = self._find_level0_token(start, end, sep)
            if pos is None:
                break

            if pos > start:
                result.append((start, pos - 1))
            elif allow_blank:
                result.append((None, None))
            else:
                raise ParserError(
                    errmsg,
                    self.template.filename,
                    self.tokens[pos].line
                )

            start = pos + 1

        # Anything left is the last or only range
        if start <= end:
            result.append((start, end))
        elif allow_blank:
            result.append((None, None))
        else:
            raise ParserError(
                errmsg,
                self.template.filename,
                self.tokens[end].line if end < len(self.tokens) else 0
            )

        return result

    def _find_tag_segments(self, start, end):
        """ Return list of (start, end) for any tag segments. """
        return self._split_tokens(start, end, Token.TYPE_SEMICOLON)

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
                    raise ParserError(
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

        if len(self.action_handler_stack) > 1:
            raise ParserError(
                "Unmatched action tag",
                self.template.filename,
                self.action_handler_stack[-1][0]
            )

        return self.nodes

    def _parse_tag_action(self, start, end):
        """ Parse some action tag. """

        # Determine the action
        token = self._get_token(start, end, "Expected action")
        self.action_line = token.line

        action = token.value
        start += 1

        # Use the current handler
        handler = self.action_handler_stack[-1][1]
        handler(
            self,
            self.template,
            self.action_line,
            action,
            start,
            end
        )

    def _parse_tag_emitter(self, start, end):
        """ Parse an emitter tag. """
        expr = self._parse_expr(start, end)
        line = self.tokens[start].line

        if isinstance(expr, ValueExpr):
            node = TextNode(self.template, line, str(expr.eval(None)))
        else:
            node = EmitNode(self.template, line, expr)
        self.stack[-1].append(node)

    def _parse_expr_or_assign(self, start, end):
        """ Parse an expression or an assignment. """

        if end > start and self.tokens[start + 1].type == Token.TYPE_ASSIGN:
            return self._parse_assign(start, end)

        return (None, self._parse_expr(start, end))

    def _parse_expr(self, start, end):
        # pylint: disable=too-many-locals
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
                raise ParserError(
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
                return AndExpr(
                    self.template,
                    token.line,
                    expr1,
                    expr2
                )
            return OrExpr(
                self.template,
                token.line,
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
                self.template,
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
                self.template,
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
                self.template,
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
                    self.template,
                    token.line,
                    lambda a: not a,
                    self._parse_expr(nott + 1, end)
                )
            raise ParserError(
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

                return UnaryExpr(
                    self.template,
                    token.line,
                    lambda a: -a,
                    self._parse_expr(posneg + 1, end)
                )

            raise ParserError(
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
            expr = self._parse_expr_list_dict(start + 1, closing - 1)

            if closing < end:
                expr = self._parse_continuation(expr, closing + 1, end)

            return expr

        if token.type == Token.TYPE_WORD:
            # Variable
            var = self._get_token_var(start, end, allow_type=True)
            expr = VarExpr(self.template, token.line, var)

            if start < end:
                expr = self._parse_continuation(expr, start + 1, end)

            return expr

        if token.type in (Token.TYPE_STRING, Token.TYPE_INTEGER, Token.TYPE_FLOAT):
            expr = ValueExpr(self.template, token.line, token.value)

            if start < end:
                expr = self._parse_continuation(expr, start + 1, end)

            return expr

        raise ParserError(
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

                raise ParserError(
                    "Expected variable name",
                    self.template.filename,
                    token.line
                )

            if token.type == Token.TYPE_OPEN_PAREN:
                closing = self._find_level0_closing(start, end)
                if start < closing - 1:
                    exprs = self._parse_multi_expr(start + 1, closing - 1, allow_assign=True)
                else:
                    exprs = []
                expr = FuncExpr(self.template, token.line, expr, exprs)
                start = closing + 1
                continue

            if token.type == Token.TYPE_OPEN_BRACKET:
                closing = self._find_level0_closing(start, end)
                expr1 = self._parse_multi_expr(start + 1, closing - 1, allow_blank=True)
                if len(expr1) == 1 and expr1[0] is not None:
                    expr = LookupItemExpr(self.template, token.line, expr, expr1[0])
                elif len(expr1) == 2 or len(expr1) == 3:
                    expr = LookupSliceExpr(self.template, token.line, expr, expr1)
                else:
                    raise SyntaxError(
                        "Invalid item or slice lookup",
                        self.template.filename,
                        token.line
                    )
                start = closing + 1
                continue

            raise ParserError(
                "Unexpected token",
                self.template.filename,
                token.line
                )

        return expr

    def _parse_expr_list_dict(self, start, end):
        """ Pare an expression that's a list or dictionary. """
        line = self.tokens[start - 1].line if start > 0 else 0
        keys = []
        values = []

        # Special cases first
        if end == start - 1:
            # [] - empty list
            return ListExpr(self.template, line, [])

        if start == end and self.tokens[start].type == Token.TYPE_COLON:
            # [:] - empty dict
            return DictExpr(self.template, line, [], [])

        # Process the parts
        splits = self._split_tokens(start, end, Token.TYPE_COMMA)
        is_dict = None

        for (split_start, split_end) in splits:
            # Determine if we are a dictionary, if we don't already know
            if is_dict is None:
                pos = self._find_level0_token(
                    split_start, split_end, Token.TYPE_COLON
                )
                is_dict = pos is not None

            # If dict, get the key
            if is_dict:
                pos = self._find_level0_token(
                    split_start, split_end, Token.TYPE_COLON
                )
                if pos is None:
                    raise ParserError(
                        "Dictionary expecting ':'",
                        self.template.filename,
                        line
                    )

                keys.append(self._parse_expr(
                    split_start, pos - 1
                ))
                value_start = pos + 1
            else:
                value_start = split_start

            # Get the value
            values.append(self._parse_expr(value_start, split_end))


        # We no longer return ValueExpr even if the list is all ValueExpr
        # It was an optimization, but since the reference is to a mutable list
        # The value of the ValueExpr's result could be change then another
        # iteration on the same set tag could have a different value.
        # ValueExpr should only be used for immutable values for this reason
        if is_dict:
            return DictExpr(self.template, line, keys, values)

        return ListExpr(self.template, line, values)

    def _parse_multi_expr(self, start, end, allow_blank=False, allow_assign=False):
        """ Parse a list of expressions separated by comma. """

        splits = self._split_tokens(start, end, Token.TYPE_COMMA, allow_blank=allow_blank)

        if splits:
            items = []
            for (split_start, split_end) in splits:
                if split_start is None or split_end is None:
                    items.append(None)
                elif allow_assign:
                    items.append(self._parse_expr_or_assign(
                        split_start, split_end
                    ))
                else:
                    items.append(self._parse_expr(
                        split_start, split_end
                    ))
            return items

        raise ParserError(
            "Expected expression list",
            self.template.filename,
            self.tokens[start - 1] if start > 0 else 0
        )

    def _parse_assign(self, start, end, allow_type=False):
        """ Parse a var = expr assignment, return (var, expr) """
        var = self._get_token_var(start, end, allow_type=allow_type)
        start += 1

        self._get_expected_token(start, end, Token.TYPE_ASSIGN, "Expected '='")
        start += 1

        expr = self._parse_expr(start, end)

        return (var, expr)

    def _parse_multi_assign(self, start, end, allow_type=False):
        """ Parse multiple var = expr statemetns, return [(var, expr)] """

        splits = self._split_tokens(start, end, Token.TYPE_COMMA)
        if splits:
            assigns = []
            for (split_start, split_end) in splits:
                assigns.append(self._parse_assign(
                    split_start, split_end, allow_type=allow_type
                ))

            return assigns

        raise ParserError(
            "Expected assignment list.",
            self.template.filename,
            self.tokens[start - 1].line if start > 0 else 0
        )

    def _parse_multi_var(self, start, end, allow_type=False):
        """ Parse multiple variables and return [var] """

        splits = self._split_tokens(start, end, Token.TYPE_COMMA)
        if splits:
            varlist = []
            for (split_start, split_end) in splits:
                varlist.append(self._get_token_var(
                    split_start, split_end, allow_type=allow_type
                    ))
                self._get_no_more_tokens(split_start + 1, split_end)

            return varlist

        raise ParserError(
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
                        nl = 1 if pre_ws_control == Token.WS_TRIMTONL else 0 # pylint: disable=invalid-name
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
                        nl = 0 if post_ws_control == Token.WS_TRIMTONL else 1 # pylint: disable=invalid-name
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
