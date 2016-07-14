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
        self._pre_strip = False

    def parse(self):
        """ Parse the template and return the node list. """
        
        self._parse_body()
        self._flush_buffer()

        if self._ops_stack:
            self._syntax_error(
                "Unmatched action tag", 
                self._ops_stack[-1][0],
                self._ops_stack[-1][1]
            )

        return self._nodes

    def _parse_body(self):
        """ Parse the entire body. """

        last = 0
        while True:

            pos = self._text.find("{", last)
            if pos == -1:
                # No more tags
                self._buffer.append(self._text[last:])
                return
            else:
                # Found the start of a tag
                text = self._text[last:pos]
                self._line += text.count("\n")
                self._buffer.append(self._text[last:pos])

                last = self._parse_tag(pos)

    def _parse_tag(self, pos):
        """ Parse a tag found at pos """
        tag = self._text[pos:pos + 2]
        if not tag in ("{#", "{%", "{{"):
            raise SyntaxError(
                "Unknown tag {0}".format(tag),
                self._template._filename,
                self._line
            )

        start = tag + 2
        if self._text[start:start + 1] == "-":
            post_strip = True
            start += 1
        else:
            post_strip = False

        self._flush_buffer(post_strip)
        if tag == "{#":
            return self._parse_tag_comment(start)
        elif tag == "{%":
            return self._parse_tag_action(start)
        elif tag == "{{":
            return self._parse_tag_emitter(start)

    def _parse_tag_ending(self, start, ending, bare=True):
        """ Parse an expected tag ending. """

        # Find out ending
        pos = self._text.find(ending, start)
        if pos == -1:
            raise SyntaxError(
                "Expecting end tag: {0}".format(ending),
                self._template._filename,
                self._line
            )

        # Make sure only whitespace was before it
        guts = self._text[start:pos + 2]
        if bare and (guts.strip() != ending):
            raise SyntaxError(
                "Expecting end tag: {0}".format(ending),
                self._template._filename,
                self._line
            )
            

        if (pos - 1 > start) and (self._text[pos - 1:pos] == "-"):
            self._pre_strip = True

        self._line += guts.count("\n")
        return pos + 2

    def _parse_tag_comment(self, start):
        """ Parse a comment tag: """

        return self._parse_tag_ending(start, "#}", False)

    def _parse_tag_action(self, start):
        """ Parse some action tag. """
        
        # Determine the action
        pos = self._skip_space(start, "Incomplete tag")
        end = self._find_space(pos, "Incomplete tag")
        action = self._text[pos:end]
        
        if action == "if":
            return self._parse_action_if(end)
        elif action == "else":
            return self._parse_action_else(end)
        elif action == "for":
            return self._parse_action_for(end)
        elif action == "set":
            return self._parse_action_set(end)
        elif action == "with":
            return self._parse_action_with(end)
        elif action == "include":
            return self._parse_action_include(end)
        elif action == "set":
            return self._parse_action_set(end)
        elif action == "section":
            return self._parse_action_section(end)
        elif action == "use":
            return self._parse_action_use(end)
        elif action.startswith("end"):
            return self._parse_action_end(end)
        else:
            raise SyntaxError(
                "Unknown action tag: {0}".format(action),
                self._template._filename,
                self._line
            )

    def _parse_action_if(self, start):
        """ Parse an if action. """
        line = self._line
        pos = self._skip_space(start, "Expected expression")
        (expr, pos) = self._parse_expr(pos)
        pos = self._parse_tag_ending("%}")
        
        node = IfNode(self._template, line, expr)
        
        self._stack[-1].append(node)
        self._stack.append(node._nodes)
        return pos

    def _parse_action_else(self, start):
        """ Parse an else. """
        line = self._line
        pos = self._parse_tag_ending("%}")

        if not self._ops_stack:
            raise SyntaxError(
                "Mismatched else",
                self._template._filename,
                line
            )

        what = self._ops_stack[-1]
        if what[0] != "if":
            raise SyntaxError(
                "Mismatched else",
                self._template._filename,
                line
            )

        self._stack.pop()
        node = self._stack[-1][-1]
        self._stack.append(node._else)
        return pos

    def _parse_tag_emitter(self, start):
        pass

    def _skip_space(self, start, errmsg=None):
        """ Return the first non-whitespace position. """
        for pos in range(start, len(self._text)):
            ch = self._text[pos]
            if ch == "\n":
                self._line += 1
            elif ch in (" ", "\t"):
                continue

            return pos

        if errmsg:
            raise SyntaxError(
                errmsg,
                self._template._filename,
                self._line
            )

        return -1

    def _find_space(self, start, errmsg=None):
        """ Find the next space, do not increase line number. """
        for pos in range(start, len(self._text)):
            if self._text[pos] in ("\n", " ", "\t"):
                return pos
        
        if errmsg:
            raise SyntaxError(
                errmsg,
                self._template._filename,
                self._line
            )

        return -1

    def _parse_expression(self, start):
        """ Parse an expression and return (node, pos) """
        pass




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
                # Handle if we are in a string or not
                if escaped:
                    escaped = False
                    continue

                if text[pos] == "\"":
                    quoted = not quoted
                    continue

                if quoted:
                    if text[pos] == "\\":
                        escaped = True
                    continue

                # At this point, we should not be quoted
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

                elif words[0] == "section":
                    # section <...>
                    if len(words) < 2:
                        self._syntax_error("Don't understand section", token, self._line)
                    self._ops_stack.append(["section", self._line])

                    expr = self._prep_expr("".join(words[1:]))
                    node = SectionNode(self._template, self._line, expr)
                    self._stack[-1].append(node)
                    self._stack.append(node._nodes)

                elif words[0] == "use":
                    # use <...>
                    if len(words) < 2:
                        self._syntax_error("Don't understand use", token, self._line)

                    expr = self._prep_expr("".join(words[1:]))
                    node = UseSectionNode(self._template, self._line, expr)
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


    def _flush_buffer(self, post=False):
        """ Flush the buffer to output. """
        if self._buffer:
            expr = "".join(self._buffer)

            if self._pre_strip:
                # If the previous tag had a white-space control {{ ... -}}
                # trim the start of this buffer up to/including a new line
                first_nl = expr.find("\n")
                if first_nl == -1:
                    expr = expr.lstrip()
                else:
                    expr = expr[:first_nl + 1].lstrip() + expr[first_nl + 1:]

            if post:
                # If the current tag has a white-space contro {{- ... }}
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


