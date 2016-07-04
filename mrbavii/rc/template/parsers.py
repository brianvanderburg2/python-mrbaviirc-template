# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides the parsers used by the template engine.

import re

from .errors import *
from .nodes import *
from .expr import *


class TemplateParser(object):
    """ A base tokenizer. """

    def __init__(self, template, text):
        """ Initialize the parser. """

        self._template = template
        self._text = text
        
        # Stack and line number
        self._ops_stack = []
        self._nodes = []
        self._stack = [self._nodes]
        self._line = 1

        # Buffer for plain text segments
        self._buffer = []
        self._post_strip = False

    def parse(self):
        """ Parse the template and return the node list. """
        
        self._parse_text(self._text)
        self._flush_buffer()

        if self._ops_stack:
            self._syntax_error(
                "Unmatched action tag", 
                self._ops_stack[-1][0],
                self._ops_stack[-1][1]
            )

        return self._nodes

    def _parse_text_tokens(self, text):
        """ Parse the text into a series of tokens. """
        last = 0

        while True:
            start = text.find("{", last)

            if start == -1:
                # No token found
                yield text[last:]
                return

            if start > last:
                # Token found, text before it
                yield text[last:start]

            # Now we are in the token
            kind = text[start + 1:start + 2]
            if not kind in ("%", "{", "#"):
                self._syntax_error("Unkown token type", kind, self._line)
            
            # Find the end of the token
            quoted = False
            escaped = False
            found = False

            for pos in range(start + 2, len(text)):
                if escaped:
                    escaped = False
                    continue

                if text[pos] == "\"":
                    quoted = not quoted
                    continue

                if quoted:
                    continue

                if text[pos] == "}":

                    if text[pos+1:pos+2] == "}" and kind == "{":
                        # // Found }} with opening {{
                        # Skip this char because next char is the real end
                        kind = "}"
                        continue
                        
                    if text[pos - 1] == kind and pos - 1 > start + 1:
                        yield text[start:pos + 1]
                        last = pos + 1
                        found = True
                        break
                    else:
                        self._syntax_error("Mismatch token close tag", text[pos - 1], self._line)

            if not found:
                self._syntax_error("Unclosed token", kind, self._line)

    def _parse_text(self, text):
        """ Parse the template from the text and build the node list. """

        for token in self._parse_text_tokens(text):
            # How many new lines
            line_count = token.count("\n")

            if token.startswith("{#"):
                # Just a comment
                if not token.endswith("#}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(pre, post)

            elif token.startswith("{{"):
                # Output some value
                if not token.endswith("}}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(pre, post)

                if token in ("{{", "{#", "{%"):
                    # Allow for literal tags.
                    node = TextNode(self._template, self._line,token)
                else:
                    # Create the expression node
                    expr = self._prep_expr(token)
                    node = VarNode(self._template, self._line, expr)

                self._stack[-1].append(node)

            elif token.startswith("{%"):
                # An action
                if not token.endswith("%}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(pre, post)
                
                words = token.split()

                if words[0] == "if":
                    # if <expr>
                    if len(words) < 2:
                        self._syntax_error("Don't understand if", token, self._line)
                    self._ops_stack.append(["if", self._line])

                    expr = self._prep_expr("".join(words[1:]))
                    node = IfNode(self._template, self._line, expr)
                    
                    self._stack[-1].append(node)
                    self._stack.append(node._if)

                elif words[0] == "else":
                    # else
                    if len(words) != 1:
                        self._syntax_error("Don't understand else", token, self._line)

                    if not self._ops_stack:
                        self._syntax_error("Mismatched else", token, self._line)
                    start_what = self._ops_stack[-1]
                    if start_what[0] != "if":
                        self._syntax_error("Mismatched else", token, self._line)

                    self._stack.pop()
                    node = self._stack[-1][-1]
                    self._stack.append(node._else)

                elif words[0] == "for":
                    # for <variable> in <expr>
                    if len(words) < 4 or words[2] != "in":
                        self._syntax_error("Don't understarnd for", token, self._line)
                    self._ops_stack.append(["for", self._line])

                    var = self._variable(words[1], False)
                    expr = self._prep_expr("".join(words[3:]))
                    node = ForNode(self._template, self._line, var, expr)

                    self._stack[-1].append(node)
                    self._stack.append(node._nodes)

                elif words[0] == "include":
                    # include <filename>
                    if len(words) != 2:
                        self._syntax_error("Don't understand include", token, self._line)

                    filename = words[1]
                    node = IncludeNode(self._template, self._line, filename)
                    self._stack[-1].append(node)

                elif words[0] == "with":
                    # with
                    if len(words) != 1:
                        self._syntax_error("Don't understand with", token, self._line)

                    self._ops_stack.append(["with", self._line])
                    node = WithNode(self._template, self._line)
                    self._stack[-1].append(node)
                    self._stack.append(node._nodes)

                elif words[0] == "set":
                    # set var = var.subvar.subsubvar, set var
                    if len(words) == 2:
                        var = self._variable(words[1], False)
                        node = SetNode(self._template, self._line, var, True)
                        self._stack[-1].append(node)

                    elif len(words) < 4 or words[2] != "=":
                        self._syntax_error("Don't understand set", token, self._line)

                    else:
                        var = self._variable(words[1], False)
                        expr = self._prep_expr("".join(words[3:]))
                        node = AssignNode(self._template, self._line, var, expr)

                        self._stack[-1].append(node)

                elif words[0] == "unset":
                    # unset <var>
                    if len(words) != 2:
                        self._syntax_error("Don't understand unset", token, self._line)

                    var = self._variable(words[1], False)
                    node = SetNode(self._template, self._line, var, False)

                    self._stack[-1].append(node)

                elif words[0].startswith("end"):
                    if len(words) != 1:
                        self._syntax_error("Don't understand end", token, self._line)

                    end_what = words[0][3:]
                    if not self._ops_stack:
                        self._syntax_error("Too many ends", token, self._line)
                    start_what = self._ops_stack.pop()
                    if start_what[0] != end_what:
                        self._syntax_error("Mismatched end tag", end_what, self._line)

                    # Next nodes go to the previous level
                    self._stack.pop()

                else:
                    self._syntax_error("Don't understand tag", words[0], self._line)

            else:
                #Literal content
                if token:
                    self._buffer.append(token)

            # Increase line count after processing
            self._line += line_count


    def _flush_buffer(self, pre=False, post=False):
        """ Flush the buffer to output. """
        if self._buffer:
            expr = "".join(self._buffer)

            if self._post_strip:
                # If the previous tag had a post-strip {{ ... -}}
                # trim the start of this buffer up to/including a new line
                first_nl = expr.find("\n")
                if first_nl == -1:
                    expr = expr.lstrip()
                else:
                    expr = expr[:first_nl + 1].lstrip() + expr[first_nl + 1:]

            if pre:
                # If the current tag has a pre-strip {{- ... }}
                # trim the end of the buffer up to/including a new line
                last_nl = expr.find("\n")
                if last_nl == -1:
                    expr = expr.rstrip()
                else:
                    expr = expr[:last_nl] + expr[last_nl:].rstrip()
            
            if expr:
                node = TextNode(self._template, self._line, expr)
                self._stack[-1].append(node)

        self._buffer = []
        self._post_strip = post # Store this tag's post-strip for the next flush

    def _read_token(self, token):
        """ Read a token and whitepsace control. """

        if token[2:3] == "-":
            pre = True
            start = 3
        else:
            pre = False
            start = 2

        if token[-3:-2] == "-":
            post = True
            end = -3
        else:
            post = False
            end = -2

        return (pre, post, token[start:end].strip())
    
    def _prep_expr(self, text):
        """ Prepare an expression text. """
        
        # Strip out whitespace
        text = "".join(text.split())

        return self._do_expr(text)

    def _do_expr(self, text):
        """ The real expression parsing is here. """

        if len(text) == 0:
            self._syntax_error("Expecting an expression", text, self._line)

        elif "|" in text:
            pipes = text.split("|")
            expr = self._do_expr(pipes[0])
            for pipe in pipes[1:]:
                (filter, params) = self._parse_pipe(pipe)
                self._variable(filter, False)

                expr = FilterExpr(self._template, self._line, expr, filter, params)

        elif self._is_int(text):
            expr = ValueExpr(self._template, self._line, int(text))

        else:
            var = self._variable(text)
            expr = VarExpr(self._template, self._line, var)

        return expr

    def _parse_pipe(self, text):
        """ Parse a text for filters """

        start = text.find("(")
        if start == -1:
            return (text, [])

        func = text[0:start]
        end = text.rfind(")")
        if end != len(text) - 1:
            self._syntax_error("Don't understand pipe", text, self._line)

        params = []
        for param in text[start + 1:end].split(","):
            params.append(self._do_expr(param))

        return (func, params)

    def _is_int(self, text):
        """ Return true if the string is an integer. """
        try:
            value = int(text)
            return True
        except ValueError:
            return False

    def _syntax_error(self, msg, thing, where):
        """ Raise an error if something is wrong. """

        raise SyntaxError(
            "{0}: {1}".format(msg, thing),
            self._template._filename,
            where
        )

    def _variable(self, what, allow_dots=True):
        """ Check that a variable is valid form. """
        if allow_dots:
            result = []
            for part in what.split("."):
                if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*$", part):
                    self._syntax_error("Not a valid name", what, self._line)
                result.append(part)
            return tuple(result)
        else:
            if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*$", what):
                self._syntax_error("Not a valid name", what, self._line)
            return what


