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


import os
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
        names = {}
        exec(str(self), names)

        return names


class Environment(object):
    """ represent a template environment. """

    def __init__(self, *contexts):
        """ Initialize the template environment. """

        self._context = {}
        for context in contexts:
            self._context.update(context)

        self._saved_contexts = []
        self._cache = {}

    def load_file(self, filename):
        """ Load a template from a file. """

        abspath = os.path.abspath(os.path.normpath(filename))
        if not abspath in self._cache:
            self._cache[abspath] = Template(self, filename=abspath)

        return self._cache[abspath]

    def load_string(self, string):
        """ Load a template from a string. """
        return Template(self, string=string)

    def save_context(self):
        """ Save the current context. """
        self._saved_contexts.append(dict(self._context))

    def restore_context(self):
        """ Restore a saved context. """
        self._context = self._saved_contexts.pop()

    def do_dots(self, value, *dots):
        """ Evaluate dotted expressions. """
        for dot in dots:
            try:
                value = getattr(value, dot)
            except AttributeError:
                value = value[dot]
            if callable(value):
                value = value()
        return value


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

    def __init__(self, env, string=None, filename=None):
        """ Initialize a template with context variables. """
        
        # Initialize
        self._filename = filename

        if string is None:
            if self._filename is None:
                raise Error("Filename must be specified if text is not.")
            string = open(self._filename, "rU").read()

        # Remember the environment
        self._env = env

        # Stack and line number
        self._ops_stack = []
        self._line = 0

        # Buffer for plain text segments
        self._buffer = []
        self._post_strip = False

        # Manage the code we are building.
        code = CodeBuilder()


        code.add_line("def render_function(env, owner, outresult=None):")
        code.indent()

        code.add_line("if outresult is None:")
        code.indent()
        code.add_line("result = []")
        code.dedent()
        code.add_line("else:")
        code.indent()
        code.add_line("result = outresult")
        code.dedent()

        code.add_line("append_result = result.append")
        code.add_line("extend_result = result.extend")
        code.add_line("to_str = str")
        code.add_line("try_offsets = []")
        body_code = code.add_section()
        
        code.add_line("if outresult is None:")
        code.indent()
        code.add_line("return ''.join(result)")
        code.dedent()
        
        code.dedent()

        self._build_code(string, body_code)

        # Extract the render function
        self._code = str(code)
        self._globals = code.get_globals()
        self._render_function = self._globals["render_function"]

    def _build_code(self, string, code):
        """ Build the code for the template. """

        # Split tokens
        for linetext in string.splitlines():
            if self._line > 0:
                self._buffer.append("\n")
            self._line += 1
            self._build_line(linetext, code)

        if self._ops_stack:
            self._syntax_error(
                "Unmatched action tag", 
                self._ops_stack[-1][0],
                self._ops_stack[-1][1]
            )

        self._flush_buffer(code)

    def _build_line(self, string, code):
        """ Build code from a single line. """

        for token in re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", string):

            if token.startswith("{#"):
                # Just a comment
                if not token.endswith("#}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(code, pre, post)
                continue

            elif token.startswith("{{"):
                # Output some value
                if not token.endswith("}}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(code, pre, post)

                expr = self._prep_expr([token])
                code.add_line("append_result(to_str({0}))".format(expr))
            
            elif token.startswith("{%"):
                # An action
                if not token.endswith("%}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(code, pre, post)
                
                words = token.split()

                if words[0] == "include":
                    # include <filename>
                    if len(words) != 2:
                        self._syntax_error("Don't understand include", token, self._line)

                    filename = words[1] # TODO: CHECK THIS FOR FILENAME SANITY
                    code.add_line("owner._include({0}, result)".format(repr(filename)))
                
                elif words[0] == "set":
                    # set <variable> = <condition...>
                    if len(words) < 4 or words[2] != "=":
                        self._syntax_error("Don't understand set", token, self._line)

                    self._variable(words[1])
                    code.add_line("env._context[{0}] = {1}".format(
                            repr(words[1]),
                            self._prep_expr(words[3:]),
                        )
                    )

                elif words[0] == "unset":
                    # unset <variable>
                    if len(words) != 2:
                        self._syntax_error("Don't understand unset", token, self._line)

                    self._variable(words[1])
                    code.add_line("env._context.pop({0}, None)".format(repr(words[1])))

                elif words[0] == "try":
                    # try
                    if len(words) != 1:
                        self._syntax_error("Don't understand try", token, self._line)
                    self._ops_stack.append(["try", self._line])
                    code.add_line("try_offsets.append(len(result))")
                    code.add_line("try:")
                    code.indent()

                elif words[0] == "with":
                    # with
                    if len(words) != 1:
                        self._syntax_error("Don't understand with", token, self._line)
                    self._ops_stack.append(["with", self._line])
                    code.add_line("env.save_context()")

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
                        "for env._context[{0}] in {1}:".format(
                            repr(words[1]),
                            self._prep_expr(words[3:])
                        )
                    )
                    code.indent()

                elif words[0] == "continue":
                    # continue
                    if len(words) != 1:
                        self._syntax_error("Don't understand continue", token, self._line)
                    
                    if not self._ops_stack:
                        self._syntax_error("Mismatched continue", token, self._line)
                    start_what = self._ops_stack[-1]
                    if start_what[0] != "for":
                        self._syntax_error("Mismatched continue", token, self._line)

                    code.add_line("continue")

                elif words[0] == "break":
                    # break
                    if len(words) != 1:
                        self._syntax_error("Don't understand break", token, self._line)
                    
                    if not self._ops_stack:
                        self._syntax_error("Mismatched break", token, self._line)
                    start_what = self._ops_stack[-1]
                    if start_what[0] != "for":
                        self._syntax_error("Mismatched break", token, self._line)

                    code.add_line("break")

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
                        code.add_line("env.restore_context()")
                    elif end_what == "try":
                        code.add_line("pass")
                        code.dedent()
                        code.add_line("except (AttributeError, KeyError) as e:")
                        code.indent()
                        code.add_line("if result:")
                        code.indent()
                        code.add_line("del result[try_offsets[-1]:]")
                        code.dedent()
                        code.dedent()
                        code.add_line("finally:")
                        code.indent()
                        code.add_line("try_offsets.pop()")
                        code.dedent()

                    else:
                        code.add_line("pass")
                        code.dedent()
                else:
                    self._syntax_error("Don't understand tag", words[0], self._line)

            else:
                #Literal content
                if token:
                    self._buffer.append(token)

    def _flush_buffer(self, code, pre=False, post=False):
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
                code.add_line("append_result({0})".format(repr(expr)))

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
                    code = "env._context[{0}]({1},{2})".format(repr(func), code, ",".join(params_code))
                else:
                    code = "env._context[{0}]({1})".format(repr(func), code)

        elif "." in expr:
            dots = expr.split(".")
            code = self._expr_code(dots[0])
            args = ", ".join(repr(d) for d in dots[1:])
            code = "env.do_dots({0}, {1})".format(code, args)

        elif self._isint(expr):
            code = repr(int(expr))

        else:
            self._variable(expr)
            code = "env._context[{0}]".format(repr(expr))

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
        env = self._env
        env.save_context()
        try:
            if context:
                env._context.update(context)
            return self._render_function(env, self, result)
        finally:
            env.restore_context()


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

    def _include(self, filename, result):
        """ Include another template. """
        if self._filename is None:
            raise Error("Can't include a template if a filename isn't specified.")

        newfile = os.path.join(os.path.dirname(self._filename), *(filename.split("/")))
        t = self._env.load_file(newfile)
        t.render(None, result)



# Test
################################################################################

# TODO

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Template Test")
    parser.add_argument("-c", dest="code", action="store_true", default=False, help="Output the generated code")
    parser.add_argument("template", help="Location of the template")
    parser.add_argument("data", nargs="?", help="Location of the data json")

    args = parser.parse_args()

    context = {
        "first": lambda x: x[0],
        "last": lambda x: x[-1],
        "upper": lambda x: x.upper(),
        "lower": lambda x: x.lower(),
        "join": lambda x, y: y.join(x),
        "split": lambda x, y: x.split(y)
    }

    e = Environment(context)
    t = e.load_file(args.template)
    if args.code:
        print(t._code)
    else:
        import json
        data = json.loads(open(args.data).read())
        print(t.render(data))

        


