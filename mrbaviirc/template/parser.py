""" A parser for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import re


from .errors import *
from .nodes import *
from .expr import *
from .scope import *


class Token(object):
    """ Represent a token. """
    TYPE_TEXT           = 1
    TYPE_START_COMMENT  = 2
    TYPE_END_COMMENT    = 3
    TYPE_START_ACTION   = 4
    TYPE_END_ACTION     = 5
    TYPE_START_EMITTER  = 6
    TYPE_END_EMITTER    = 7
    TYPE_STRING         = 8
    TYPE_INTEGER        = 9
    TYPE_FLOAT          = 10
    TYPE_OPEN_BRACKET   = 11
    TYPE_CLOSE_BRACKET  = 12
    TYPE_OPEN_PAREN     = 13
    TYPE_CLOSE_PAREN    = 14
    TYPE_COMMA          = 15
    TYPE_ASSIGN         = 16
    TYPE_PLUS           = 17
    TYPE_MINUS          = 18
    TYPE_MULTIPLY       = 19
    TYPE_DIVIDE         = 20
    TYPE_MODULUS        = 21
    TYPE_EQUAL          = 22
    TYPE_GREATER        = 23
    TYPE_GREATER_EQUAL  = 24
    TYPE_LESS           = 25
    TYPE_LESS_EQUAL     = 26
    TYPE_NOT_EQUAL      = 27
    TYPE_DOT            = 29
    TYPE_NOT            = 30
    TYPE_WORD           = 31
    TYPE_SEMICOLON      = 32
    TYPE_AND            = 33
    TYPE_OR             = 34

    WS_NONE = 0
    WS_TRIMTONL = 1
    WS_TRIMTONL_PRESERVENL = 2
    WS_ADDNL = 3
    WS_ADDSP = 4

    def __init__(self, type, line, value=None):
        """ Initialize a token. """
        self._type = type
        self._line = line
        self._value = value


class Tokenizer(object):
    """ Parse text into some tokens. """
    MODE_TEXT       = 1
    MODE_COMMENT    = 2
    MODE_OTHER      = 3

    _alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    _digit = "0123456789"

    _symbol_map = {
        "[": Token.TYPE_OPEN_BRACKET,
        "]": Token.TYPE_CLOSE_BRACKET,
        "(": Token.TYPE_OPEN_PAREN,
        ")": Token.TYPE_CLOSE_PAREN,
        ",": Token.TYPE_COMMA,
    }

    _tag_map = {
        "{#": Token.TYPE_START_COMMENT,
        "{%": Token.TYPE_START_ACTION,
        "{{": Token.TYPE_START_EMITTER,
        "#}": Token.TYPE_END_COMMENT,
        "%}": Token.TYPE_END_ACTION,
        "}}": Token.TYPE_END_EMITTER
    }

    _ws_map = {
        "-": Token.WS_TRIMTONL,
        "^": Token.WS_TRIMTONL_PRESERVENL,
        "+": Token.WS_ADDNL,
        "*": Token.WS_ADDSP
    }

    def __init__(self, text, filename):
        """ Initialze the tokenizer. """
        self._text = text
        self._filename = filename
        self._line = 1
        self._mode = self.MODE_TEXT
        self._tokens = []

    def parse(self):
        """ Parse the tokens and return the sequence. """

        self._mode = self.MODE_TEXT
        pos = 0

        while pos < len(self._text):
            if self._mode == self.MODE_TEXT:
                pos = self._parse_mode_text(pos)

            elif self._mode == self.MODE_COMMENT:
                pos = self._parse_mode_comment(pos)

            else:
                pos = self._parse_mode_other(pos)

        return self._tokens


    def _parse_mode_text(self, start):
        """ Parse while in text mode. """
        # Search for open block. If not a tag, pass through as a normal block.
        # Makes text containing { and } easier. To pass litteral {{, {#, or {%,
        # use {{ "{{" }} in the template
        pos = start
        while True:
            pos = self._text.find("{", pos)
            if pos == -1:
                break

            tag = self._text[pos:pos + 2]

            if tag in self._tag_map:
                break

            # Skip non-tags to allow literal text to contain {
                
            pos += 2
            continue

        # Add any preceeding text
        if pos == -1:
            block = self._text[start:]
        else:
            block = self._text[start:pos]

        if block:
            token = Token(Token.TYPE_TEXT, self._line, block)
            self._tokens.append(token)
            self._line += block.count("\n")

        if pos == -1:
            # No more tags
            return len(self._text)

        # Get whitespace control
        wscontrol = self._ws_map.get(self._text[pos + 2:pos + 3], Token.WS_NONE)

        # Create token
        type = self._tag_map[tag]
        token = Token(type, self._line, wscontrol)
        self._tokens.append(token)
        if type == Token.TYPE_START_COMMENT:
            self._mode = self.MODE_COMMENT
        else:
            self._mode = self.MODE_OTHER

        # Return next position
        if wscontrol != Token.WS_NONE:
            return pos + 3
        else:
            return pos + 2

    def _parse_mode_comment(self, start):
        """ Parse a comment tag. """

        # Just look for the ending
        pos = self._text.find("#}", start)

        if pos == -1:
            # No more tokens
            self._line += self._text[start:].count("\n")
            self._mode = self.MODE_TEXT
            return len(self._text)

        else:
            wscontrol = self._ws_map.get(self._text[pos - 1], Token.WS_NONE)

            self._line += self._text[start:pos].count("\n")
            token = Token(Token.TYPE_END_COMMENT, self._line, wscontrol)

            self._tokens.append(token)
            self._mode = self.MODE_TEXT
            return pos + 2

    def _parse_mode_other(self, start):
        """ Parse other stuff. """

        pos = start
        while pos < len(self._text):
            ch = self._text[pos]

            # Whitespace is ignored
            if ch in (" ", "\t", "\n"):
                if ch == "\n":
                    self._line += 1

                pos += 1
                continue

            # [
            if ch == "[":
                self._tokens.append(Token(Token.TYPE_OPEN_BRACKET, self._line))
                pos += 1
                continue

            # ]
            if ch == "]":
                self._tokens.append(Token(Token.TYPE_CLOSE_BRACKET, self._line))
                pos += 1
                continue
 
            # (
            if ch == "(":
                self._tokens.append(Token(Token.TYPE_OPEN_PAREN, self._line))
                pos += 1
                continue

            # )
            if ch == ")":
                self._tokens.append(Token(Token.TYPE_CLOSE_PAREN, self._line))
                pos += 1
                continue

            # ,
            if ch == ",":
                self._tokens.append(Token(Token.TYPE_COMMA, self._line))
                pos += 1
                continue

            # = and ==
            if ch == "=":
                if self._text[pos + 1:pos + 2] == "=":
                    self._tokens.append(Token(Token.TYPE_EQUAL, self._line))
                    pos += 2
                    continue
                else:
                    self._tokens.append(Token(Token.TYPE_ASSIGN, self._line))
                    pos += 1
                    continue

            # + and +<number>
            if ch == "+":
                if self._text[pos + 1:pos + 2] in (self._digit + "."):
                    pos = self._parse_number(pos)
                    continue
                elif self._text[pos + 1:pos + 3] not in ("#}", "%}", "}}"):
                    self._tokens.append(Token(Token.TYPE_PLUS, self._line))
                    pos += 1
                    continue
            
            # - and -<number>
            if ch == "-":
                if self._text[pos + 1:pos + 2] in (self._digit + "."):
                    pos = self._parse_number(pos)
                    continue
                elif self._text[pos + 1:pos + 3] not in ("#}", "%}", "}}"):
                    self._tokens.append(Token(Token.TYPE_MINUS, self._line))
                    pos += 1
                    continue

            # *
            if ch == "*":
                if self._text[pos + 1:pos + 3] not in ("#}", "%}", "}}"):
                    self._tokens.append(Token(Token.TYPE_MINUS, self._line))
                    pos += 1
                    continue

            # /
            if ch == "/":
                self._tokens.append(Token(Token.TYPE_DIVIDE, self._line))
                pos += 1
                continue

            # %
            if ch == "%":
                if self._text[pos:pos + 2] != "%}":
                    self._tokens.append(Token(Token.TYPE_MODULUS, self._line))
                    pos += 1
                    continue

            # > and >=
            if ch == ">":
                if self._text[pos + 1, pos + 2] == "=":
                    self._tokens.append(Token(Token.TYPE_GREATER_EQUAL, self._line))
                    pos += 2
                    continue
                else:
                    self._tokens.append(Token(Token.TYPE_GREATER, self._line))
                    pos += 1
                    continue

            # < and <= and <>
            if ch == "<":
                if self._text[pos + 1:pos + 2] == "=":
                    self._tokens.append(Token(Token.TYPE_LESS_EQUAL, self._line))
                    pos += 2
                    continue
                elif self._text[pos + 1:pos + 2] == ">":
                    self._tokens.append(Token(Token.TYPE_NOT_EQUAL, self._line))
                    pos += 2
                    continue
                else:
                    self._tokens.append(Token(Token.TYPE_LESS, self._line))
                    pos += 1
                    continue

            # ;
            if ch == ";":
                self._tokens.append(Token(Token.TYPE_SEMICOLON, self._line))
                pos += 1
                continue

            # . and .<number>
            if ch == ".":
                if self._text[pos + 1:pos + 2] in self._digit:
                    pos = self._parse_number(pos)
                    continue
                else:
                    self._tokens.append(Token(Token.TYPE_DOT, self._line))
                    pos += 1
                    continue

            # !
            if self._text[pos:pos + 3] == "!":
                self._tokens.append(Token(Token.TYPE_NOT, self._line))
                pos += 1
                continue

            # <number>
            if ch in self._digit:
                pos = self._parse_number(pos)
                continue

            # "<string>"
            if ch == "\"":
                pos = self._parse_string(pos)
                continue

            # word
            if ch in self._alpha or ch == "_":
                pos = self._parse_word(pos)
                continue

            # Ending tag, no whitespace control
            if self._text[pos:pos + 2] in ("#}", "%}", "}}"):
                type = self._tag_map[self._text[pos:pos + 2]]
                self._tokens.append(Token(type, self._line, Token.WS_NONE))
                self._mode = self.MODE_TEXT
                pos += 2
                break

            # Ending tag, with whitespace control
            if ch in self._ws_map:
                if self._text[pos + 1:pos + 3] in ("#}", "%}", "}}"):
                    type = self._tag_map[self._text[pos + 1:pos + 3]]
                    wscontrol = self._ws_map[ch]
                    self._tokens.append(Token(type, self._line, wscontrol))
                    self._mode = self.MODE_TEXT
                    pos += 3
                    break

            # Unknown character in input
            raise SyntaxError(
                "Unexpected character {0}".format(ch),
                self._filename,
                self._line
            )

        # end while loop
        return pos

    def _parse_number(self, start):
        """ Parse a number. """
        result = []
        found_dot = False

        if self._text[start] == "-":
            start += 1
            result.append("-")
        elif self._text[start] == "+":
            start += 1

        for pos in range(start, len(self._text)):
            ch = self._text[pos]

            if ch in self._digit:
                result.append(ch)
                continue

            if ch == ".":
                if found_dot:
                    break

                result.append(ch)
                found_dot = True
                continue

            break

        result = "".join(result)
        if found_dot:
            token = Token(Token.TYPE_FLOAT, self._line, float(result))
        else:
            token = Token(Token.TYPE_INTEGER, self._line, int(result))

        self._tokens.append(token)
        return pos

    def _parse_string(self, start):
        """ Parse a string. """

        escaped = False
        result = []
        end = False
        for pos in range(start + 1, len(self._text)): # Skip opening quote
            ch = self._text[pos]

            if escaped:
                escaped = False
                if ch == "n":
                    result.append("\n")
                elif ch == "t":
                    result.append("\t")
                elif ch == "\\":
                    result.append("\\")
                elif ch == "\"":
                    result.append("\"")
                continue

            if ch == "\"":
                end = True
                break

            if ch == "\\":
                escaped = True
                continue

            result.append(ch)
            if ch == "\n":
                self._line += 1

        if not end:
            raise SyntaxError("Unclosed string", self._filename, self._line)

        token = Token(Token.TYPE_STRING, self._line, "".join(result))
        self._tokens.append(token)
        return pos + 1

    def _parse_word(self, start):
        """ Parse a word. """
        result = []
        for pos in range(start, len(self._text)):
            ch = self._text[pos]

            if ch in self._alpha or ch in self._digit or ch in ("_", "@", "#"):
                result.append(ch)
                continue
            else:
                break

        token = Token(Token.TYPE_WORD, self._line, "".join(result))
        self._tokens.append(token)

        return pos


class TemplateParser(object):
    """ A base tokenizer. """

    AUTOSTRIP_NONE = 0
    AUTOSTRIP_STRIP = 1
    AUTOSTRIP_TRIM = 2

    _open_close_map = {
        Token.TYPE_OPEN_PAREN: Token.TYPE_CLOSE_PAREN,
        Token.TYPE_OPEN_BRACKET: Token.TYPE_CLOSE_BRACKET
    }

    _close_tokens = [
        Token.TYPE_CLOSE_PAREN,
        Token.TYPE_CLOSE_BRACKET
    ]   

    def __init__(self, template, text):
        """ Initialize the parser. """

        self._template = template
        self._text = text
        self._tokens = None
        
        # Stack and line number
        self._ops_stack = []
        self._nodes = NodeList()
        self._stack = [self._nodes]

        # Buffer for plain text segments
        self._buffer = []
        self._pre_ws_control = Token.WS_NONE
        self._autostrip = self.AUTOSTRIP_NONE
        self._autostrip_stack = []

    def _get_token(self, pos, end, errmsg="Expected token"):
        """ Get a token at a position, raise error if not found/out of bound """

        if pos <= end:
            return self._tokens[pos]
        else:
            raise SyntaxError(
                errmsg,
                self._template._filename,
                self._tokens[pos - 1]._line if pos > 0 else 0
            )


    def _get_expected_token(self, pos, end, types, errmsg="Unexpected token", values=[]):
        """ Expect a specific type of token. """

        token = self._get_token(pos, end, errmsg)
        if not isinstance(types, (list, tuple)):
            types = [types]

        if token._type not in types:
            raise SyntaxError(
                errmsg,
                self._template._filename,
                token._line
            )

        if token._type == token.TYPE_WORD:
            if not isinstance(values, (list, tuple)):
                values = [values]

            if token._value not in values:
                raise SyntaxError(
                    errmsg,
                    self._template._filename,
                    token._line
                )

        return token

    def _get_no_more_tokens(self, pos, end, errmsg="Unexpected token"):
        """ Expect the end of the range. """

        if pos <= end:
            raise SyntaxError(
                errmsg,
                self._template._filename,
                self._tokens[pos]._line
            )

    def _get_token_var(self, pos, end, errmsg="Expected variable."):
        """ Parse a variable and return var """

        errpos = pos - 1
        if pos <= end:
            errpos = pos
            token = self._tokens[pos]
            if token._type == Token.TYPE_WORD:
                if re.match("[a-zA-Z_][a-zA-Z0-9_]*", token._value):
                    return token._value
                else:
                    raise SyntaxError(
                        "Invalid variable name: {0}".format(token._value),
                        self._template._filename,
                        self._template._line
                    )
         
        # If we got here, it wasn't a variable
        raise SyntaxError(
            errmsg,
            self._template._filename,
            self._tokens[errpos] if errpos > 0 else 0
        )

    def _find_level0_token(self, start, end, token=None):
        """ Find a token at level 0 nesting. """

        token_stack = []
        first = None

        for pos in range(start, end + 1):
            newtoken = self._tokens[pos]

            if newtoken._type in self._open_close_map:
                # Found an open token
                token_stack.append(newtoken._type)
                if len(token_stack) == 1:
                    first = pos

            elif newtoken._type in self._close_tokens:
                # Make sure it matches the
                if len(token_stack):
                    last = token_stack.pop()
                else:
                    last = None

                if last is None or newtoken._type != self._open_close_map[last]:
                    raise SyntaxError(
                        "Mismatched or unclosed token",
                        self._template._filename,
                        newtoken._line
                    )

            elif len(token_stack) == 0:
                if token is None or token == newtoken._type:
                    return pos

        if token_stack:
            raise SyntaxError(
                "Unmatched braces/parenthesis",
                self._template._filename,
                self._tokens[first]._line
            )

        return None

    def _find_level0_closing(self, start, end):
        """ Find the matching closing token. """

        token = self._tokens[start]
        if not token._type in self._open_close_map:
            raise SyntaxError(
                "Unexpected token",
                self._template._filename,
                token._line
            )

        token_stack = [token._type]

        for pos in range(start + 1, end + 1):
            token = self._tokens[pos]
            
            if token._type in self._open_close_map:
                token_stack.append(token._type)

            elif token._type in self._close_tokens:
                if len(token_stack):
                    last = token_stack.pop()
                else:
                    last = None

                if last is None or token._type != self._open_close_map[last]:
                    raise SyntaxError(
                        "Mismatched or unclosed token",
                        self._template._filename,
                        token._line
                    )

                if len(token_stack) == 0:
                    # Popped of the start token, so this is the closing
                    return pos

        # If we get here, we never found the closing token
        raise SyntaxError(
            "Unmatched braces/parenthesis",
            self._template._filename,
            self._tokens[start]._line
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
                    self._template._filename,
                    self._tokens[pos]._line # find_level0 doesn't use get_token
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
        tokenizer = Tokenizer(self._text, self._template._filename)
        self._tokens = tokenizer.parse()

        # Parse our body
        pre_ws_control = None
        pos = 0
        while pos < len(self._tokens):
            token = self._tokens[pos]

            if token._type == Token.TYPE_TEXT:
                self._buffer.append(token._value)
                pos += 1
                continue

            if token._type in (Token.TYPE_START_COMMENT,
                               Token.TYPE_START_ACTION,
                               Token.TYPE_START_EMITTER):
                # Flush the buffer
                self._flush_buffer(pre_ws_control, token._value)

                # Find the ending
                if token._type == Token.TYPE_START_COMMENT:
                    ending = Token.TYPE_END_COMMENT
                elif token._type == Token.TYPE_START_ACTION:
                    ending = Token.TYPE_END_ACTION
                elif token._type == Token.TYPE_START_EMITTER:
                    ending = Token.TYPE_END_EMITTER

                for endpos in range(pos + 1, len(self._tokens)):
                    if self._tokens[endpos]._type == ending:
                        break
                else:
                    raise SyntaxError(
                        "Opening tag missing closing tag.",
                        self._template._filename,
                        token._line
                    )

                end_token = self._tokens[endpos]
                pre_ws_control = end_token._value

                # Parse the insides
                if token._type == Token.TYPE_START_ACTION:
                    self._parse_tag_action(pos + 1, endpos - 1)

                elif token._type == Token.TYPE_START_EMITTER:
                    self._parse_tag_emitter(pos + 1, endpos - 1)

                # comment is skipped entirely

                # Move past it
                pos = endpos + 1
        
        self._flush_buffer(pre_ws_control, None)

        if self._ops_stack:
            raise SyntaxError(
                "Unmatched action tag", 
                self._template._filename,
                self._ops_stack[-1][1]
            )

        return self._nodes

    def _parse_tag_action(self, start, end):
        """ Parse some action tag. """
        
        # Determine the action
        token = self._get_token(start, end, "Expected action")
        action = token._value
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
            self._autostrip = self.AUTOSTRIP_STRIP
        elif action == "autotrim":
            self._autostrip = self.AUTOSTRIP_TRIM
        elif action == "no_autostrip":
            self._autostrip = self.AUTOSTRIP_NONE
        else:
            raise SyntaxError(
                "Unknown action tag: {0}".format(action),
                self._template._filename,
                token._line
            )

    def _parse_action_if(self, start, end):
        """ Parse an if action. """
        expr = self._parse_expr(start, end)
        line = self._tokens[start]._line
        
        node = IfNode(self._template, line, expr)
        
        self._ops_stack.append(("if", line))
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

    def _parse_action_elif(self, start, end):
        """ Parse an elif action. """
        expr = self._parse_expr(start, end)
        line = self._tokens[start]._line

        if not self._ops_stack:
            raise SyntaxError(
                "Mismatched elif",
                self._template._filename,
                line
            )

        what = self._ops_stack[-1]
        if what[0] != "if":
            raise SyntaxError(
                "Mismatched elif",
                self._template._filename,
                line
            )

        self._stack.pop()
        node = self._stack[-1][-1]
        node.add_elif(expr)
        self._stack.append(node._nodes)

    def _parse_action_else(self, start, end):
        """ Parse an else. """

        self._get_no_more_tokens(start, end)
        line = self._tokens[start - 1]._line if start > 0 else 0

        if not self._ops_stack:
            raise SyntaxError(
                "Mismatched else",
                self._template._filename,
                line
            )

        what = self._ops_stack[-1]
        if not what[0] in ("if", "for"):
            raise SyntaxError(
                "Mismatched else",
                self._template._filename,
                line
            )

        # Both if and for do this the same way
        self._stack.pop()
        node = self._stack[-1][-1]
        node.add_else()
        self._stack.append(node._nodes)

    def _parse_action_break(self, start, end):
        """ Parse break. """
        
        self._get_no_more_tokens(start, end)
        line = self._tokens[start - 1]._line if start > 0 else 0
        
        node = BreakNode(self._template, line)
        self._stack[-1].append(node)

    def _parse_action_continue(self, start, end):
        """ Parse continue. """

        self._get_no_more_tokens(start, end)
        line = self._tokens[start - 1]._line if start > 0 else 0
        
        node = ContinueNode(self._template, line)
        self._stack[-1].append(node)

        return start

    def _parse_action_for(self, start, end):
        """ Parse a for statement. """
        # TODO: with new segments, support for <a>[,<b>] in expr and also
        # for init ; test ; step (init and step are multi-assign, test is expr)
        # Or, simplification, change for to foreach, both can still have else
        # foreach if there are no results, for if first test is false/no iterations
        # and break to break out of loop

        var = self._get_token_var(start, end)
        line = self._tokens[start]._line
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
        if token._type == Token.TYPE_COMMA:

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

        node = ForNode(self._template, line, var, cvar, expr)
        self._ops_stack.append(("for", line))
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

    def _parse_action_switch(self, start, end):
        """ Parse a switch statement. """
        expr = self._parse_expr(start, end)
        line = self._tokens[start]._line

        node = SwitchNode(self._template, line, expr)
        self._ops_stack.append(("switch", line))
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

    def _parse_action_switch_item(self, start, end, item):
        """ Parse the switch item. """
        line = self._tokens[start - 1]._line if start > 0 else 0

        if not self._ops_stack:
            raise SyntaxError(
                "{0} can only occur in switch".format(item),
                self._template._filename,
                line
            )

        what = self._ops_stack[-1]
        if what[0] != "switch":
            raise SyntaxError(
                "{0} can only occur in switch".format(item),
                self._template._filename,
                line
            )

        offset = SwitchNode.types.index(item)
        argc = SwitchNode.argc[offset]

        exprs = self._parse_multi_expr(start, end)

        if len(exprs) != argc:
            raise SyntaxError(
                "Switch clause {0} takes {1} argument".format(item, argc),
                self._template._filename,
                line
            )

        self._stack.pop()
        node = self._stack[-1][-1]
        node.add_case(SwitchNode.cbs[offset], exprs)
        self._stack.append(node._nodes)

    def _parse_action_set(self, start, end, where):
        """ Parse a set statement. """
        assigns = self._parse_multi_assign(start, end)
        line = self._tokens[start]._line

        node = AssignNode(self._template, line, assigns, where)
        self._stack[-1].append(node)

    def _parse_action_unset(self, start, end):
        """ Parse an unset statement. """
        varlist = self._parse_multi_var(start, end)
        line = self._tokens[start]._line

        node = UnsetNode(self._template, line, varlist);
        self._stack[-1].append(node)

    def _parse_action_scope(self, start, end):
        """ Parse a scope statement. """
        line = self._tokens[start - 1]._line if start > 0 else 0
        if start <= end:
            assigns = self._parse_multi_assign(start, end)
        else:
            assigns = []

        node = ScopeNode(self._template, line, assigns)
        self._ops_stack.append(("scope", line))
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

    def _parse_action_code(self, start, end):
        """ Parse a code node. """
        line = self._tokens[start - 1]._line if start > 0 else 0

        # disable autostrip for this block
        self._autostrip_stack.append(self._autostrip)
        self._autostrip = self.AUTOSTRIP_NONE

        retvar = None
        assigns = []
        segments = self._find_tag_segments(start, end)
        for segment in segments:
            (start, end) = segment

            token = self._get_token(start, end)
            start += 1

            # expecting either return or with
            if token._type == Token.TYPE_WORD and token._value == "return":
                retvar = self._get_token_var(start, end)
                start += 1

                self._get_no_more_tokens(start, end)
                continue

            if token._type == Token.TYPE_WORD and token._value == "with":
                assigns = self._parse_multi_assign(start, end)
                continue
            
            raise SyntaxError(
                "Unexpected token",
                self._template._filename,
                self._tokens[start]._line
            )


        self._ops_stack.append(("code", line))
        node = CodeNode(self._template, line, assigns, retvar)
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

    def _parse_action_include(self, start, end):
        """ Parse an include node. """
        line = self._tokens[start - 1]._line if start > 0 else start

        retvar = None
        assigns = []
        segments = self._find_tag_segments(start, end)
        for segment in segments:
            (start, end) = segment

            token = self._get_token(start, end)
            start += 1

            # expecting either return or with
            if token._type == Token.TYPE_WORD and token._value == "return":
                retvar = self._get_token_var(start, end)
                start += 1

                self._get_no_more_tokens(start, end)
                continue

            if token._type == Token.TYPE_WORD and token._value == "with":
                assigns = self._parse_multi_assign(start, end)
                continue

            # neither return or with, so expression
            start -= 1
            expr = self._parse_expr(start, end)


        node = IncludeNode(self._template, line, expr, assigns, retvar)
        self._stack[-1].append(node)

    def _parse_action_return(self, start, end):
        """ Parse a return variable node. """
        assigns = self._parse_multi_assign(start, end)
        line = self._tokens[start]._line

        node = ReturnNode(self._template, line, assigns)
        self._stack[-1].append(node)

    def _parse_action_expand(self, start, end):
        """ Parse an expand node. """
        expr = self._parse_expr(start, end)
        line = self._tokens[start]._line

        node = ExpandNode(self._template, line, expr)
        self._stack[-1].append(node)

    def _parse_action_section(self, start, end):
        """ Parse a section node. """
        expr = self._parse_expr(start, end)
        line = self._tokens[start]._line

        self._ops_stack.append(("section", line))
        node = SectionNode(self._template, line, expr)
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

    def _parse_action_use(self, start, end):
        """ Parse a use section node. """
        expr = self._parse_expr(start, end)
        line = self._tokens[start]._line

        node = UseSectionNode(self._template, line, expr)
        self._stack[-1].append(node)

    def _parse_action_var(self, start, end):
        """ Parse a block to store rendered output in a variable. """
        var = self._get_token_var(start, end)
        line = self._tokens[start]._line
        start += 1

        self._get_no_more_tokens(start, end)

        node = VarNode(self._template, line, var)
        self._ops_stack.append(("var", line))
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

    def _parse_action_error(self, start, end):
        """ Raise an error from the template. """
        expr = self._parse_expr(start, end)
        line = self._tokens[start]._line

        node = ErrorNode(self._template, line, expr)
        self._stack[-1].append(node)

    def _parse_action_import(self, start, end):
        """ Parse an import action. """
        assigns = self._parse_multi_assign(start, end)
        line = self._tokens[start]._line

        node = ImportNode(self._template, line, assigns)
        self._stack[-1].append(node)

    def _parse_action_do(self, start, end):
        """ Parse a do tag. """
        nodes = self._parse_multi_expr(start, end)
        line = self._tokens[start]._line

        node = DoNode(self._template, line, nodes)
        self._stack[-1].append(node)

    def _parse_action_end(self, start, end, action):
        """ Parse an end tag """
        self._get_no_more_tokens(start, end)
        line = self._tokens[start - 1]._line if start > 0 else 0

        if not self._ops_stack:
            raise SyntaxError(
                "To many ends: {0}".format(action),
                self._template._filename,
                line
            )
        elif start <= end:
            raise SyntaxError(
                "Unexpected token",
                self._template._filename,
                self._tokens[start]._line
            )

        what = self._ops_stack[-1]
        if what[0] != action[3:]:
            raise SyntaxError(
                "Mismatched end tag: {0}".format(action),
                self._template._filename,
                line
            )

        self._ops_stack.pop()

        # Handle certain tags

        # Pop node stack for any op that created a new node stack
        if not what[0] == "strip":
            self._stack.pop()

        # Restore autostrip value for any op that pushed the value
        if what[0] in ("strip", "code"):
            self._autostrip = self._autostrip_stack.pop()

    def _parse_action_strip(self, start, end):
        """ Change the autostrip state. """
        line = self._tokens[start - 1]._line if start > 0 else 0

        self._autostrip_stack.append(self._autostrip)
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

        if token._value == "on":
            self._autostrip = self.AUTOSTRIP_STRIP
        elif token._value == "trim":
            self._autostrip = self.AUTOSTRIP_TRIM
        else:
            self._autostrip = self.AUTOSTRIP_NONE

    def _parse_tag_emitter(self, start, end):
        """ Parse an emitter tag. """
        expr = self._parse_expr(start, end)
        line = self._tokens[start]._line

        if isinstance(expr, ValueExpr):
            node = TextNode(self._template, line, str(expr.eval(None)))
        else:
            node = EmitNode(self._template, line, expr)
        self._stack[-1].append(node)

    def _parse_expr(self, start, end):
        """ Parse the expression. """
        
        #fgopen = fgclose = None
        addsub = None
        muldivmod = None
        posneg = None
        andor = None
        nott = None
        compare = None
        neg = None

        pos = start
        while pos <= end:
            # Find the token
            pos = self._find_level0_token(pos, end)
            if pos is None:
                break

            token = self._tokens[pos]

            # Keep track of certain types
            # We ignore many dependency how we split

            if token._type == Token.TYPE_SEMICOLON:
                raise SyntaxError(
                    "Unexpected semicolon",
                    self._template._filename,
                    token._line
                )

            if token._type in (Token.TYPE_MULTIPLY, Token.TYPE_DIVIDE, Token.TYPE_MODULUS):
                if muldivmod is None:
                    muldivmod = pos
                pos += 1
                continue

            if token._type in (Token.TYPE_PLUS, Token.TYPE_MINUS):
                if pos == start:
                    # At start, it is a positive or negative
                    if posneg is None:
                        posneg = pos
                else:
                    lasttoken = self._tokens[pos - 1]
                    if lasttoken._type in (
                        Token.TYPE_ASSIGN, Token.TYPE_PLUS, Token.TYPE_MINUS,
                        Token.TYPE_MULTIPLE, Token.TYPE_DIVIDE, Token.TYPE_MODULUS,
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
                pos +=1
                continue

            if token._type in (
                Token.TYPE_EQUAL, Token.TYPE_NOT_EQUAL,
                Token.TYPE_GREATER, Token.TYPE_GREATER_EQUAL,
                Token.TYPE_LESS, Token.TYPE_LESS_EQUAL
            ):
                if compare is None:
                    compare = pos
                pos +=1
                continue

            if token._type in (Token.TYPE_AND, Token.TYPE_OR):
                if andor is None:
                    andor = pos
                pos += 1
                continue

            if token._type == Token.TYPE_NOT:
                nott = pos
                pos += 1
                continue

            # Unrecognized token is okay here
            pos += 1
            continue


        # Now we handle things based on what we found

        # Split on and/or first
        #if andor is not None:
        #    expr1 = self._parse_expr(start, andor - 1)
        #    expr2 = self._parse_expr(andor + 1, end)
        #    # TODO: create andor node

        # Split on comparison next
        #if compare is not None
        #    expr1 = self._parse_expr(start, compare - 1)
        #   expr2 = self._parse_expr(compare + 1, end)

        # Add/sub next
        #if addsub is not None
        #    expr1 = self._parse_expr(start, addsub - 1)
        #    expr2 = self._parse_expr(addsub + 1, end)

        # Mul/div/mod next
        # ...

        # At this point, no more binary operators

        # Not
        # if nott is not None
        #   if nott == start
        #       ...
        #   else
        #       raise expection

        # Pos/neg
        # if posneg is not None:
        #   if posnext == start
        #       ...
        #   else
        #       raise expection

        # Check what we have at the start
        token = self._tokens[start]

        if token._type == Token.TYPE_OPEN_PAREN:
            # Find closing paren, treat all as expression
            closing = self._find_level0_closing(start, end)
            expr = self._parse_expression(start + 1, closing - 1)

            if closing < end:
                expr = self._parse_continuation(expr, closing + 1, end)

            return expr

        if token._type == Token.TYPE_OPEN_BRACKET:
            # Find closing bracket
            closing = self._find_level0_closing(start, end)
            expr = self._parse_expr_list(start + 1, closing - 1)

            if closing < end:
                expr = self._parse_continuation(expr, closing + 1, end)

            return expr

        if token._type == Token.TYPE_WORD:
            # Variable
            var = self._get_token_var(start, end)
            expr = VarExpr(self._template, token._line, var)

            if start < end:
                expr = self._parse_continuation(expr, start + 1, end)

            return expr

        if token._type in (Token.TYPE_STRING, Token.TYPE_INTEGER, Token.TYPE_FLOAT):
            expr = ValueExpr(self._template, token._line, token._value)
            
            if start < end:
                expr = self._parse_continuation(expr, start + 1, end)
            
            return expr

        raise SyntaxError(
            "Unexpected token",
            self._template._filename,
            token._line
        )

    def _parse_continuation(self, expr, start, end):
        """ Parse a continuation of an expression. """

        while start <= end:
            token = self._tokens[start]

            if token._type == Token.TYPE_DOT:
                start += 1
                if start <= end:
                    var = self._get_token_var(start, end)
                    expr = LookupAttrExpr(self._template, token._line, expr, var)
                    start += 1
                    continue
                    
                raise SyntaxError(
                    "Expected variable name",
                    self._template._filename,
                    token._line
                )

            if token._type == Token.TYPE_OPEN_PAREN:
                closing = self._find_level0_closing(start, end)
                exprs = self._parse_multi_expr(start + 1, closing - 1)
                expr = FuncExpr(self._template, token._line, expr, exprs)
                start = closing + 1
                continue

            if token._type == Token.TYPE_OPEN_BRACKET:
                closing = self._find_level0_closing(start, end)
                expr1 = self._parse_expr(start + 1, closing - 1)
                expr = LookupItemExpr(self._template, token._line, expr, expr1)
                start = closing + 1
                continue

            raise SyntaxError(
                "Unexpected token",
                self._template._filename,
                token._line
                )

        return expr

    def _parse_expr_list(self, start, end):
        """ Pare an expression that's a list. """
        line = self._tokens[start - 1]._line if start > 0 else 0
        if start <= end:
            nodes = self._parse_multi_expr(start, end)
        else:
            nodes = []

        if nodes and all(isinstance(node, ValueExpr) for node in nodes):
            node = ValueExpr(self._template, nodes[0]._line, [node.eval(None) for node in nodes])
        else:
            node = ListExpr(self._template, line, nodes)
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
                self._template._filename,
                self._tokens[start - 1] if start > 0 else 0
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
                self._template._filename,
                self._tokens[start - 1]._line if start > 0 else 0
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
                    self._get_expect_token(start, end, Token.TYPE_COMMA)
                    start += 1

            return varlist
        else:
            raise SyntaxError(
                "Expected variable list",
                self._template._filename,
                self._tokens[start - 1] if start > 0 else 0
            )

    def _flush_buffer(self, pre_ws_control, post_ws_control):
        """ Flush the buffer to output. """
        text = ""
        if self._buffer:
            text = "".join(self._buffer)

            if self._autostrip == self.AUTOSTRIP_STRIP:
                text = text.strip()
            elif self._autostrip == self.AUTOSTRIP_TRIM:
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
            node = TextNode(self._template, 0, text)
            self._stack[-1].append(node)

        self._buffer = []

