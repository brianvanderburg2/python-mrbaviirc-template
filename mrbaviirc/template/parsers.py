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

        # Find our ending
        pos = self._text.find(ending, start)
        if pos == -1:
            raise SyntaxError(
                "Expecting end tag: {0}".format(ending),
                self._template._filename,
                self._line
            )
            
        if (pos  > start) and (self._text[pos - 1:pos] == "-"):
            self._pre_strip = True
            ending = "-" + ending

        # Make sure only whitespace was before it
        guts = self._text[start:pos + 2]
        if bare and (guts.strip() != ending):
            raise SyntaxError(
                "Expecting end tag: {0}".format(ending),
                self._template._filename,
                self._line
            )

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
            pos =  self._parse_action_if(end)
        elif action == "else":
            pos =  self._parse_action_else(end)
        elif action == "for":
            pos =  self._parse_action_for(end)
        elif action == "set":
            pos =  self._parse_action_set(end)
        elif action == "with":
            pos =  self._parse_action_with(end)
        elif action == "include":
            pos =  self._parse_action_include(end)
        elif action == "section":
            pos =  self._parse_action_section(end)
        elif action == "use":
            pos =  self._parse_action_use(end)
        elif action.startswith("end"):
            pos =  self._parse_action_end(end, action)
        else:
            raise SyntaxError(
                "Unknown action tag: {0}".format(action),
                self._template._filename,
                self._line
            )

        return self._parse_tag_ending(pos, "%}")

    def _parse_action_if(self, start):
        """ Parse an if action. """
        line = self._line
        pos = self._skip_space(start, "Expected expression")
        (expr, pos) = self._parse_expr(pos)
        
        node = IfNode(self._template, line, expr)
        
        self._ops_stack.append(("if", line))
        self._stack[-1].append(node)
        self._stack.append(node._nodes)
        return pos

    def _parse_action_else(self, start):
        """ Parse an else. """
        line = self._line

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

    def _parse_action_for(self, start):
        """ Parse a for statement. """
        line = self._line

        pos = self._skip_space(start, "Expected variable")
        (var, pos) = self._parse_var(pos, False)

        pos = self._skip_word(pos, "in", "Expected 'in'")

        (expr, pos) = self._parse_expr(pos)

        node = ForNode(self._template, line, var, expr)
        self._ops_stack.append(("for", line))
        self._stack[-1].append(node)
        self._stack.append(node._nodes)
        return pos
    
    def _parse_action_set(self, start):
        """ Parse a set statement. """
        line = self._line

        pos = self._skip_space(start, "Expected variable")
        (var, pos) = self._parse_var(pos, False)

        pos = self._skip_word(pos, "=", "Expected '='")

        (expr, pos) = self._parse_expr(pos)

        node = AssignNode(self._template, line, var, expr)
        self._stack[-1].append(node)
        return pos

    def _parse_action_with(self, start):
        """ Parse a with statement. """
        line = self._line

        self._ops_stack.append(("with", line))

        node = WithNode(self._template, line)
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

        return pos

    def _parse_action_include(self, start):
        """ Parse an include node. """
        line = self._line

        pos = self._skip_space(start, "Expecting string")
        if self._text[pos] != "\"":
            raise SyntaxError(
                "Expecting string",
                self._template._filename,
                line
            )

        (path, pos) = self._parse_string(pos)

        node = IncludeNode(self._template, line, path)
        self._stack[-1].append(node)

        return pos

    def _parse_action_section(self, start):
        """ Parse a section node. """
        line = self._line

        pos = self._skip_space(start, "Expecting expression")
        (expr, pos) = self._parse_expr(pos)

        self._ops_stack.append(("section", line))
        node = SectionNode(self._template, line, expr)
        self._stack[-1].append(node)
        self._stack.append(node._nodes)

        return post

    def _parse_action_use(self, start):
        """ Parse a use section node. """
        line = self._line

        pos = self._skip_space(start, "Expecting expression")
        (expr, pos) = self._parse_expr(pos)

        node = UseSectionNode(self._template, line, expr)
        self._stack[-1].append(node)
        return pos

    def _parse_action_end(self, start, action):
        """ Parse an end tag """
        line = self._line

        if not self._ops_stack:
            raise SyntaxError(
                "To many ends: {0}".format(action),
                self._template._filename,
                line
            )

        what = self._ops_stack[-1]
        if what[0] != action[3:]:
            raise SyntaxError(
                "Mismatched end tag: {0}".format(action),
                self._template._filename,
                line
            )

        self._stack.pop()
        return pos

    def _parse_tag_emitter(self, start):
        """ Parse an emitter tag. """
        line = self._line

        pos = self._skip_space(pos, "Expected expression")
        (expr, pos) = self._parse_expr(pos)
        pos = self._parse_ending_tag(pos, "}}")

        node = VarNode(self._template, line, expr)
        self._stack[-1].append(node)
        return pos
        
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

    def _skip_word(self, start, word, errmsg=None):
        """ Skip a word. """
        pos = self._skip_space(start, errmsg)
        if pos == -1:
            return -1

        end = self._find_space(pos, errmsg):
        if pos == -1:
            return -1

        if self._text[pos:end] == word:
            return end

        if errmsg:
            raise SyntaxError(
                errmsg,
                self._template._filename,
                line
            )

        return -1

    def _parse_expr(self, start):
        """ Parse an expression and return (node, pos) """
        pass

    def _parse_string(self, start):
        """ Parse a string and return (str, pos) """

        if self._text[start:start + 1] != "\"":
            raise SyntaxError(
                "Expected string",
                self._template._filename,
                self._line
            )

        escaped = False
        result = []
        for pos in range(start + 1,len(self._text)):
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
                return ("".join(result), pos + 1)

            if ch == "\\":
                escaped = True
                continue

            result.append(ch)

        raise SyntaxError(
            "Expected end of string",
            self._template._filename,
            self._line
        )

    def _parse_var(self, start, allow_dots=True):
        """ Parse a variable and return (var, pos) """

        first = True
        result = []
        current = []
        for pos in range(start, len(self._text)):
            ch = self._text[pos]

            if ch == ".":
                if not allow_dots:
                    raise SyntaxError(
                        "Dotted variable not allowed",
                        self._template._filename,
                        self._line
                    )

                if not current:
                    raise SyntaxError(
                        "Expected variable segment",
                        self._template._filename,
                        self._line
                    )

                result.append("".join(current))
                current = []
                first = True
                continue

            if ch in ("abcdefghijklmnopqrstuvwxyz"
                      "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                      "0123456789_"):

                if first and ch in "0123456789":
                    raise SyntaxError(
                        "Expected variable",
                        self._template._filename,
                        self._line
                    )

                current.append(ch)
                first = False
            else:
                break

        if first == True:
            raise SyntaxError(
                "Epected variable",
                self._template._filename
                self._line
            )

        if allow_dots:
            result.append("".join(current))
            return (result, pos)
        else:
            return ("".join(current), pos)
                


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


