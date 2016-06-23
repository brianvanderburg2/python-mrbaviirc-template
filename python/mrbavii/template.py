#!/usr/bin/env python
#
# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides a simple light-weight template engine.


# License
################################################################################
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# Credits
################################################################################

# Templite
#------------------------------------------------------------------------------
# Portions of the code below are based on the Templite code that is part of the
# 500 lines or less project.


# Template engine
################################################################################


import sys
import os
import argparse
import re

try:
    from codecs import open
except ImportError:
    pass



class Error(Exception):
    """ Base template engine error. """
    pass


class CodeBuilder(object):
    """ Represent code to be compiled. """

    INDENT_SIZE = 4

    def __init__(self, indent=0):
        """ Initialize the code fragment with a specific indentation level. """
        self._code = []
        self._indent = indent

    def __str__(self):
        """ Return the single string representation of the code. """
        return "".join(str(c) for c in self._code)

    def indent(self):
        """ Increase the indentation level. """
        self._indent += self.INDENT_SIZE

    def dedent(self):
        """ Decrease the indention level. """
        if self._indent <= 0:
            raise Error("Unable to dedent more than indented.")

        self._indent -= self.INDENT_SIZE

    def add_section(self):
        """ Add a new section to the code.  Additional code can be added
            to the section later. """
        code = CodeBuilder(self._indent)
        self._code.append(code)
        return code

    def add_line(self, line):
        """ Add a new line to the code at the current indent level. """
        self._code.extend([" " * self._indent, line, "\n"])

    def get_globals(self):
        """ Return the globals defined within the code. """
        assert self._indent == 0;
        print(str(self))
        names = {}
        exec(str(self), names)

        return names


class Template(object):
    """ Simple template parser and renderer.

    Extended variable access:

        {{ expression }}

        Expression:

            [variable or value] [ | function [(variable or value, ...)] ]*

        For example:

            {{ value }}

            {{ value | upper }}

            {{ value | index(12) }}

            {{ value | index(other.value) | upper }}

            {{ | random(1, 10) }} {# No value was used on purpose. #}

    Loops:

        {% for var in expression %}
        {% endfor %}

    Conditions:

        {% if expression %}
        {% elif expression %}
        {% else %}
        {% endif %}

    Set a variable

        {% set var = expresssion %}

    Comments:

        {# This is a commend. #}

    Whitespace control.  A "-" after an opening block will eat any preceeding
    whitespace up to and including the previous new line:

        {#- ... #}
        {{- ... }}
        {%- ... %}
    """

    def __init__(self, text=None, filename=None, *contexts):
        """ Initialize a template with context variables. """
        
        # Initialize
        self._filename = filename

        if text is None:
            if self._filename is None:
                raise Error("Filename must be specified if text is not.")
            text = open(self._filename, "rU").read()

        # Copy all contexts into our context
        self._context = {}
        for context in contexts:
            self._context.update(context)

        # Stack and line number
        self._ops_stack = []
        self._line = 0

        # Manage the code we are building.
        code = CodeBuilder()

        code.add_line("def render_function(owner, context, outresult=None):")
        code.indent()

        code.add_line("if outresult is None:")
        code.indent()
        code.add_line("result = []")
        code.dedent()
        code.add_line("else:")
        code.indent()
        code.add_line("result = outresult")
        code.dedent()

        code.add_line("saved_contexts = []")
        code.add_line("append_result = result.append")
        code.add_line("extend_result = result.extend")
        code.add_line("to_str = str")
        body_code = code.add_section()
        
        code.add_line("if outresult is None:")
        code.indent()
        code.add_line("return ''.join(result)")
        code.dedent()
        
        code.dedent()

        self._build_code(text, body_code)

        # Extract the render function
        self._render_function = code.get_globals()["render_function"]

    def _build_code(self, text, code):
        """ Build the code for the template. """

        # Split tokens
        for linetext in text.splitlines():
            if self._line > 0:
                code.add_line("append_result('\\n')")
            self._line += 1
            self._build_line(linetext, code)

        if self._ops_stack:
            self._syntax_error(
                "Unmatched action tag", 
                self.ops_stack[-1][0],
                self._ops_stack[-1][1]
            )


    def _build_line(self, text, code):
        """ Build code from a single line. """

        for token in re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text):

            if token.startswith("{#"):
                # Just a comment
                self._whitespace_control(token, code)
                continue

            elif token.startswith("{{"):
                # Output some value
                token = self._whitespace_control(token, code)

                expr = self._prep_expr([token])
                code.add_line("append_result(to_str({0}))".format(expr))
            
            elif token.startswith("{%"):
                # An action
                token = self._whitespace_control(token, code)
                
                words = token.split()

                if words[0] == "include":
                    # include <filename>
                    if len(words) != 2:
                        self._syntax_error("Don't understand include", token, self._line)

                    filename = words[1] # TODO: CHECK THIS FOR FILENAME SANITY
                    code.add_line("owner._include({0}, context, result)".format(repr(filename)))
                
                elif words[0] == "set":
                    # set <variable> = <condition...>
                    if len(words) < 4 or words[2] != "=":
                        self._syntax_error("Don't understand set", token, self._line)

                    self._variable(words[1])
                    code.add_line("context[{0}] = {1}".format(
                            repr(words[1]),
                            self._prep_expr(words[3:]),
                        )
                    )

                elif words[0] == "with":
                    # with
                    if len(words) != 1:
                        self._syntax_error("Don't understand with", token, self._line)
                    self._ops_stack.append(["with", self._line])
                    code.add_line("saved_contexts.append(dict(context))")

                elif words[0] == "if":
                    # if <condition...>
                    if len(words) < 2:
                        self._syntax_error("Don't understand if", token, self._line)
                    self._ops_stack.append(["if", self._line])
                    expr = self._prep_expr(words[1:])
                    code.add_line("if {0}:".format(expr))
                    code.indent()

                elif words[0] == "elif":
                    # elif <condition...>
                    if len(words) < 2:
                        self._syntax_error("Don't understand elif", token, self._line)

                    if not self._ops_stack:
                        self._syntax_error("Mismatched elif", token, self._line)
                    start_what = self._ops_stack[-1]
                    if start_what[0] != "if":
                        self._syntax_error("Mismatched elif", token, self._line)

                    expr = self._prep_expr(words[1:])
                    code.dedent()
                    code.add_line("elif {0}:".format(expr))
                    code.indent()

                elif words[0] == "else":
                    # else
                    if len(words) != 1:
                        self._syntax_error("Don't understand else", token, self._line)

                    if not self._ops_stack:
                        self._syntax_error("Mismatched else", token, self._line)
                    start_what = self._ops_stack[-1]
                    if start_what[0] != "if":
                        self._syntax_error("Mismatched else", token, self._line)

                    code.dedent()
                    code.add_line("else:")
                    code.indent()

                elif words[0] == "for":
                    # for <variable> in <condition...>
                    if len(words) < 4 or words[2] != "in":
                        self._syntax_error("Don't understarnd for", token, self._line)
                    self._ops_stack.append(["for", self._line])
                    self._variable(words[1])
                    code.add_line(
                        "for context[{0}] in {1}:".format(
                            repr(words[1]),
                            self._prep_expr(words[3:])
                        )
                    )
                    code.indent()

                elif words[0].startswith("end"):
                    if len(words) != 1:
                        self._syntax_error("Don't understand end", token, self._line)

                    end_what = words[0][3:]
                    if not self._ops_stack:
                        self._syntax_error("Too many ends", token, self._line)
                    start_what = self._ops_stack.pop()
                    if start_what[0] != end_what:
                        self._syntax_error("Mismatched end tag", end_what, self._line)

                    if end_what == "with":
                        code.add_line("context = saved_contexts.pop()")
                    else:
                        code.dedent()
                else:
                    self._syntax_error("Don't understand tag", words[0], self._line)

            else:
                #Literal content
                if token:
                    code.add_line("append_result(to_str({0}))".format(repr(token)))

    def _whitespace_control(self, token, code):
        if token[2:3] == "-":
            code.add_line("if len(result) > 0:")
            code.indent()
            code.add_line("last_nl = result[-1].rfind('\\n')")
            code.add_line("if last_nl == -1:")
            code.indent()
            code.add_line("result[-1] = result[-1].rstrip()")
            code.dedent()
            code.add_line("else:")
            code.indent()
            code.add_line("result[-1] = result[-1][:last_nl] + result[-1][last_nl:].rstrip()")
            code.dedent()
            code.dedent()
            return token[3:-2].strip()
        else:
            return token[2:-2].strip()

    def _prep_expr(self, expr):
        """ Prepare an expression by stripping whitespace and then parsing it """
        # Join all expressions, but each one may have whitespace so split it
        # into list with no whitespaces, then join them all together
        return self._expr_code("".join("".join(expr).split()))

    def _expr_code(self, expr):
        """ Create a python expression for output, if, and for. """

        if len(expr) == 0:
            code = repr("")
        elif "|" in expr:
            pipes = expr.split("|")
            code = self._expr_code(pipes[0])
            for pipe in pipes[1:]:
                (func, params) = self._parse_pipe(pipe)
                self._variable(func)

                params_code = []
                for p in params:
                    params_code.append(self._expr_code(p))
                if params_code:
                    code = "context[{0}]({1},{2})".format(repr(func), code, ",".join(params_code))
                else:
                    code = "context[{0}]({1})".format(repr(func), code)

        elif "." in expr:
            dots = expr.split(".")
            code = self._expr_code(dots[0])
            args = ", ".join(repr(d) for d in dots[1:])
            code = "owner._do_dots({0}, {1})".format(code, args)

        elif self._isint(expr):
            code = repr(expr)

        else:
            self._variable(expr)
            code = "context[{0}]".format(repr(expr))

        return code

    def _isint(self, expr):
        """ Test for an integer. """
        try:
            value = int(expr)
            return True
        except ValueError as e:
            return False

    def _syntax_error(self, msg, thing, where):
        """ Raise an error if something is wrong. """

        if self._filename:
            raise Error("{0} on line {1} file {2}: - {3}".format(msg, where, self._filename, repr(thing)))
        else:
            raise Error("{0} on line {1}: - {2}".format(msg, where, repr(thing)))

    def _variable(self, what):
        """ Track a varialbe that is used. """
        if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*$", what):
            self._syntax_error("Not a valid name", what, self._line)
    
    def render(self, context=None, result=None):
        """ Render teh template. """
        render_context = dict(self._context)
        if context:
            render_context.update(context)
        return self._render_function(self, render_context, result)

    def _do_dots(self, value, *dots):
        """ Evaluate dotted expressions. """
        for dot in dots:
            try:
                value = getattr(value, dot)
            except AttributeError:
                value = value[dot]
            if callable(value):
                value = value()
        return value

    def _parse_pipe(self, pipe):
        """ Parse a pipe """
        pipe = pipe.strip()

        start = pipe.find("(")
        if start == -1:
            return (pipe, [])
        
        func = pipe[0:start]
        end = pipe.rfind(")")
        if end != len(pipe) - 1:
            raise self._syntax_error("Don't understand pipe", pipe, self._line)

        params = pipe[start + 1:end].split(",")

        return (func, params)

    def _include(self, filename, context, result):
        """ Include another template. """
        if self._filename is None:
            raise Error("Can't include a template if a filename isn't specified.")

        newfile = os.path.join(os.path.dirname(self._filename), *(filename.split("/")))
        t = Template(filename=newfile)
        t.render(context, result)



# Test
################################################################################

# TODO

