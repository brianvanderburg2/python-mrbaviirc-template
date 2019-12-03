""" Tokenize the input."""
# pylint: disable=too-few-public-methods,too-many-branches,too-many-statements

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"

__all__ = ["Token", "Tokenizer"]

from .errors import ParserError


class Token(object):
    """ Represent a token. """
    (
        TYPE_TEXT,
        TYPE_START_COMMENT,
        TYPE_END_COMMENT,
        TYPE_START_ACTION,
        TYPE_END_ACTION,
        TYPE_START_EMITTER,
        TYPE_END_EMITTER,
        TYPE_STRING,
        TYPE_INTEGER,
        TYPE_FLOAT,
        TYPE_OPEN_BRACKET,
        TYPE_CLOSE_BRACKET,
        TYPE_OPEN_PAREN,
        TYPE_CLOSE_PAREN,
        TYPE_COMMA,
        TYPE_COLON,
        TYPE_ASSIGN,
        TYPE_PLUS,
        TYPE_MINUS,
        TYPE_MULTIPLY,
        TYPE_DIVIDE,
        TYPE_MODULUS,
        TYPE_EQUAL,
        TYPE_GREATER,
        TYPE_GREATER_EQUAL,
        TYPE_LESS,
        TYPE_LESS_EQUAL,
        TYPE_NOT_EQUAL,
        TYPE_DOT,
        TYPE_NOT,
        TYPE_WORD,
        TYPE_SEMICOLON,
        TYPE_AND,
        TYPE_OR,
        TYPE_FLOORDIV
    ) = range(35)

    (
        WS_NONE,
        WS_TRIMTONL,
        WS_TRIMTONL_PRESERVENL,
        WS_ADDNL,
        WS_ADDSP
    ) = range(5)

    def __init__(self, type, line, value=None):
        """ Initialize a token. """
        self.type = type
        self.line = line
        self.value = value


class Tokenizer(object):
    """ Parse text into some tokens. """
    MODE_TEXT = 1
    MODE_COMMENT = 2
    MODE_OTHER = 3

    ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    DIGIT = "0123456789"

    TAG_MAP = {
        "{#": Token.TYPE_START_COMMENT,
        "{%": Token.TYPE_START_ACTION,
        "{{": Token.TYPE_START_EMITTER,
        "#}": Token.TYPE_END_COMMENT,
        "%}": Token.TYPE_END_ACTION,
        "}}": Token.TYPE_END_EMITTER
    }

    WS_MAP = {
        "-": Token.WS_TRIMTONL,
        "^": Token.WS_TRIMTONL_PRESERVENL,
        "+": Token.WS_ADDNL,
        "*": Token.WS_ADDSP
    }

    def __init__(self, text, filename):
        """ Initialze the tokenizer. """
        self.text = text
        self.filename = filename
        self.line = 1
        self.mode = self.MODE_TEXT
        self.tokens = []

    def parse(self):
        """ Parse the tokens and return the sequence. """

        self.mode = self.MODE_TEXT
        pos = 0

        while pos < len(self.text):
            if self.mode == self.MODE_TEXT:
                pos = self._parse_mode_text(pos)

            elif self.mode == self.MODE_COMMENT:
                pos = self._parse_mode_comment(pos)

            else:
                pos = self._parse_mode_other(pos)

        return self.tokens


    def _parse_mode_text(self, start):
        """ Parse while in text mode. """
        # Search for open block. If not a tag, pass through as a normal block.
        # Makes text containing { and } easier. To pass litteral {{, {#, or {%,
        # use {{ "{{" }} in the template
        pos = start
        while True:
            pos = self.text.find("{", pos)
            if pos == -1:
                break

            tag = self.text[pos:pos + 2]

            if tag in self.TAG_MAP:
                break

            # Skip non-tags to allow literal text to contain {
            pos += 2
            continue

        # Add any preceeding text
        if pos == -1:
            block = self.text[start:]
        else:
            block = self.text[start:pos]

        if block:
            token = Token(Token.TYPE_TEXT, self.line, block)
            self.tokens.append(token)
            self.line += block.count("\n")

        if pos == -1:
            # No more tags
            return len(self.text)

        # Get whitespace control
        wscontrol = self.WS_MAP.get(self.text[pos + 2:pos + 3], Token.WS_NONE)

        # Create token
        type = self.TAG_MAP[tag]
        token = Token(type, self.line, wscontrol)
        self.tokens.append(token)
        if type == Token.TYPE_START_COMMENT:
            self.mode = self.MODE_COMMENT
        else:
            self.mode = self.MODE_OTHER

        # Return next position
        if wscontrol != Token.WS_NONE:
            return pos + 3
        else:
            return pos + 2

    def _parse_mode_comment(self, start):
        """ Parse a comment tag. """

        # Just look for the ending
        pos = self.text.find("#}", start)

        if pos == -1:
            # No more tokens
            self.line += self.text[start:].count("\n")
            self.mode = self.MODE_TEXT
            return len(self.text)

        else:
            wscontrol = self.WS_MAP.get(self.text[pos - 1], Token.WS_NONE)

            self.line += self.text[start:pos].count("\n")
            token = Token(Token.TYPE_END_COMMENT, self.line, wscontrol)

            self.tokens.append(token)
            self.mode = self.MODE_TEXT
            return pos + 2

    def _parse_mode_other(self, start):
        """ Parse other stuff. """

        pos = start
        while pos < len(self.text):
            char = self.text[pos]

            # Whitespace is ignored
            if char in (" ", "\t", "\n"):
                if char == "\n":
                    self.line += 1

                pos += 1
                continue

            # [
            if char == "[":
                self.tokens.append(Token(Token.TYPE_OPEN_BRACKET, self.line))
                pos += 1
                continue

            # ]
            if char == "]":
                self.tokens.append(Token(Token.TYPE_CLOSE_BRACKET, self.line))
                pos += 1
                continue

            # (
            if char == "(":
                self.tokens.append(Token(Token.TYPE_OPEN_PAREN, self.line))
                pos += 1
                continue

            # )
            if char == ")":
                self.tokens.append(Token(Token.TYPE_CLOSE_PAREN, self.line))
                pos += 1
                continue

            # ,
            if char == ",":
                self.tokens.append(Token(Token.TYPE_COMMA, self.line))
                pos += 1
                continue

            # :
            if char == ":":
                self.tokens.append(Token(Token.TYPE_COLON, self.line))
                pos += 1
                continue

            # = and ==
            if char == "=":
                if self.text[pos + 1:pos + 2] == "=":
                    self.tokens.append(Token(Token.TYPE_EQUAL, self.line))
                    pos += 2
                    continue
                else:
                    self.tokens.append(Token(Token.TYPE_ASSIGN, self.line))
                    pos += 1
                    continue

            # + and +<number>
            if char == "+":
                if self.text[pos + 1:pos + 2] in self.DIGIT + ".":
                    pos = self._parse_number(pos)
                    continue
                elif self.text[pos + 1:pos + 3] not in ("#}", "%}", "}}"):
                    self.tokens.append(Token(Token.TYPE_PLUS, self.line))
                    pos += 1
                    continue

            # - and -<number>
            if char == "-":
                if self.text[pos + 1:pos + 2] in self.DIGIT + ".":
                    pos = self._parse_number(pos)
                    continue
                elif self.text[pos + 1:pos + 3] not in ("#}", "%}", "}}"):
                    self.tokens.append(Token(Token.TYPE_MINUS, self.line))
                    pos += 1
                    continue

            # *
            if char == "*":
                if self.text[pos + 1:pos + 3] not in ("#}", "%}", "}}"):
                    self.tokens.append(Token(Token.TYPE_MULTIPLY, self.line))
                    pos += 1
                    continue

            # / and //
            if char == "/":
                if self.text[pos + 1:pos + 2] == "/":
                    self.tokens.append(Token(Token.TYPE_FLOORDIV, self.line))
                    pos += 2
                    continue
                else:
                    self.tokens.append(Token(Token.TYPE_DIVIDE, self.line))
                    pos += 1
                    continue

            # %
            if char == "%":
                if self.text[pos:pos + 2] != "%}":
                    self.tokens.append(Token(Token.TYPE_MODULUS, self.line))
                    pos += 1
                    continue

            # > and >=
            if char == ">":
                if self.text[pos + 1:pos + 2] == "=":
                    self.tokens.append(Token(Token.TYPE_GREATER_EQUAL, self.line))
                    pos += 2
                    continue
                else:
                    self.tokens.append(Token(Token.TYPE_GREATER, self.line))
                    pos += 1
                    continue

            # < and <=
            if char == "<":
                if self.text[pos + 1:pos + 2] == "=":
                    self.tokens.append(Token(Token.TYPE_LESS_EQUAL, self.line))
                    pos += 2
                    continue
                else:
                    self.tokens.append(Token(Token.TYPE_LESS, self.line))
                    pos += 1
                    continue

            # ;
            if char == ";":
                self.tokens.append(Token(Token.TYPE_SEMICOLON, self.line))
                pos += 1
                continue

            # . and .<number>
            if char == ".":
                if self.text[pos + 1:pos + 2] in self.DIGIT:
                    pos = self._parse_number(pos)
                    continue
                else:
                    self.tokens.append(Token(Token.TYPE_DOT, self.line))
                    pos += 1
                    continue

            # ! and !=
            if char == "!":
                if self.text[pos + 1:pos + 2] == "=":
                    self.tokens.append(Token(Token.TYPE_NOT_EQUAL, self.line))
                    pos += 2
                    continue
                else:
                    self.tokens.append(Token(Token.TYPE_NOT, self.line))
                    pos += 1
                    continue

            # &&
            if self.text[pos:pos + 2] == "&&":
                self.tokens.append(Token(Token.TYPE_AND, self.line))
                pos += 2
                continue

            # ||
            if self.text[pos:pos + 2] == "||":
                self.tokens.append(Token(Token.TYPE_OR, self.line))
                pos += 2
                continue

            # <number>
            if char in self.DIGIT:
                pos = self._parse_number(pos)
                continue

            # "<string>"
            if char == "\"":
                pos = self._parse_string(pos)
                continue

            # word
            if char in self.ALPHA or char == "_":
                pos = self._parse_word(pos)
                continue

            # Ending tag, no whitespace control
            if self.text[pos:pos + 2] in ("#}", "%}", "}}"):
                type = self.TAG_MAP[self.text[pos:pos + 2]]
                self.tokens.append(Token(type, self.line, Token.WS_NONE))
                self.mode = self.MODE_TEXT
                pos += 2
                break

            # Ending tag, with whitespace control
            if char in self.WS_MAP:
                if self.text[pos + 1:pos + 3] in ("#}", "%}", "}}"):
                    type = self.TAG_MAP[self.text[pos + 1:pos + 3]]
                    wscontrol = self.WS_MAP[char]
                    self.tokens.append(Token(type, self.line, wscontrol))
                    self.mode = self.MODE_TEXT
                    pos += 3
                    break

            # Unknown character in input
            raise ParserError(
                "Unexpected character {0}".format(char),
                self.filename,
                self.line
            )

        # end while loop
        return pos

    def _parse_number(self, start):
        """ Parse a number. """
        result = []
        found_dot = False

        if self.text[start] == "-":
            start += 1
            result.append("-")
        elif self.text[start] == "+":
            start += 1

        pos = start # In case there's nothing in range
        for pos in range(start, len(self.text)):
            char = self.text[pos]

            if char in self.DIGIT:
                result.append(char)
                continue

            if char == ".":
                if found_dot:
                    break

                result.append(char)
                found_dot = True
                continue

            break

        result = "".join(result)
        try:
            if found_dot:
                token = Token(Token.TYPE_FLOAT, self.line, float(result))
            else:
                token = Token(Token.TYPE_INTEGER, self.line, int(result))
        except ValueError:
            raise ParserError(
                "Expected number, got {0}".format(result),
                self.filename,
                self.line
            )


        self.tokens.append(token)
        return pos

    def _parse_string(self, start):
        """ Parse a string. """

        escaped = False
        result = []
        end = False
        pos = start + 1
        for pos in range(start + 1, len(self.text)): # Skip opening quote
            char = self.text[pos]

            if escaped:
                escaped = False
                if char == "n":
                    result.append("\n")
                elif char == "t":
                    result.append("\t")
                elif char == "\\":
                    result.append("\\")
                elif char == "\"":
                    result.append("\"")
                continue

            if char == "\"":
                end = True
                break

            if char == "\\":
                escaped = True
                continue

            result.append(char)
            if char == "\n":
                self.line += 1

        if not end:
            raise ParserError("Unclosed string", self.filename, self.line)

        token = Token(Token.TYPE_STRING, self.line, "".join(result))
        self.tokens.append(token)
        return pos + 1

    def _parse_word(self, start):
        """ Parse a word. """
        result = []
        pos = start
        for pos in range(start, len(self.text)):
            char = self.text[pos]

            if char in self.ALPHA or char in self.DIGIT or char in "_@":
                result.append(char)
                continue
            else:
                break

        token = Token(Token.TYPE_WORD, self.line, "".join(result))
        self.tokens.append(token)

        return pos
