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


class Renderer(object):
    """ A renderer takes content and renders it in some fashion. """

    def __init__(self):
        """ Initialize the renderer. """
        pass

    def render(self, content):
        """ Render the content. """
        raise NotImplementedError


class Node(object):
    """ A node is a part of the expression that is rendered. """

    def __init__(self, template):
        """ Initialize the node. """
        self._template = template
        self._env = template._env

    def render(self, renderer):
        raise NotImplementedError


class TextNode(Node):
    """ A node that represents a raw block of text. """

    def __init__(self, template, text):
        """ Initialize a text node. """
        Node.__init__(self, template)
        self._text = text

    def render(self, renderer):
        """ Render content from a text node. """
        renderer.render(self._text)


class IfNode(Node):
    """ A node that manages if/elif/else. """

    def __init__(self, template, var):
        """ Initialize the if node. """
        Node.__init__(self, template)
        self._ifs = []
        self._else = None

        self.add_elif(var)

    def add_elif(self, var):
        """ Add a check to the if/elif blocks. """
        condition = [var, []]
        self._ifs.append(var)

    def add_else(self):
        """ Add an else block to the if/elif/else blocks. """
        self._else = []

    def get_current(self):
        """ Return the current target. """
        if self._else is None:
            return self._ifs[-1]
        else:
            return self._else

    def render(self, renderer):
        """ Render the if node. """
        env = self._env
        for _if in self._ifs:
            (var, actions) = _if
            if env.get(var):
                for action in actions:
                    action.render(renderer)
                break
        else:
            if self._else:
                for action in self._else:
                    action.render(renderer)


class ForNode(Node):
    """ A node for handling for loops. """

    def __init__(self, template, var1, var2):
        """ Initialize the for node. """
        Node.__init__(self, template)
        self._var1 = var1
        self._var2 = var2
        self._actions = []

    def render(self, renderer):
        """ Render the for node. """
        env = self._env

        # Iterate over each value
        var2 = env.get(self._var2)
        if var2:
            for var1 in var2:
                env.set(self._var1, var1)
                    
                # Execute each sub-node
                for action in self._actions:
                    action.render(renderer)


class VarNode(Node):
    """ A node to output some value. """

    def __init__(self, template, var, filters):
        """ Initialize the node. """
        Node.__init__(self, template)
        self._var = var
        self._filters = filters

    def render(self, renderer):
        """ Render the output. """
        env = self._env
        var = env.get(self._var)

        for filter in self._filters:
            var = env.filter(var, filter)

        renderer.render(str(var))


class Environment(object):
    """ represent a template environment. """

    def __init__(self, context=None, filters=None):
        """ Initialize the template environment. """

        self._filters = {}
        if filters:
            self._filters.update(filters)

        self._context = {}
        if context:
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

    def get(self, var):
        """ Evaluate dotted expressions. """
        try:
            value = self._context[var[0]]
            for dot in var[1:]:
                try:
                    value = getattr(value, dot)
                except AttributeError:
                    value = value[dot]
                if callable(value):
                    value = value()
            return value
        except KeyError:
            return None

    def set(self, var1, var2):
        """ Set a value in the context. """
        self._context[var1] = var2

    def filter(self, value, filter):
        """ Filter a value. """
        if filter in self._filters:
            return self._filters[filter](value)
        else:
            return value


class Template(object):
    """ Simple template parser and renderer.

    Extended variable access:

        {{ expression }}

        For example:

            {{ value.subvalue }}

            {{ value.subvalue | upper }}


    Loops:

        {% for var in list %}
        {% endfor %}

    Conditions:

        {% if var %}
        {% elif var %}
        {% else %}
        {% endif %}

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
        self._actions = []
        self._stack = [self._actions]
        self._line = 0

        # Buffer for plain text segments
        self._buffer = []
        self._post_strip = False

        
        self._build(string)

    def _build(self, string):
        """ Build the nodes for the template. """

        # Split tokens
        for linetext in string.splitlines():
            if self._line > 0:
                self._buffer.append("\n")
            self._line += 1
            self._build_line(linetext)

        if self._ops_stack:
            self._syntax_error(
                "Unmatched action tag", 
                self._ops_stack[-1][0],
                self._ops_stack[-1][1]
            )

        self._flush_buffer()

    def _build_line(self, string):
        """ Build from a single line. """

        for token in re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", string):

            if token.startswith("{#"):
                # Just a comment
                if not token.endswith("#}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(pre, post)
                continue

            elif token.startswith("{{"):
                # Output some value
                if not token.endswith("}}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(pre, post)

                # Determine filters if any
                parts = token.split("|")

                var = self._variable(parts[0])
                filters = []
                for part in parts[1:]:
                    self._variables(part, False)
                    filters.append(part)

                node = VarNode(self, var, filters)
                self._stack[-1].append(node)

            elif token.startswith("{%"):
                # An action
                if not token.endswith("%}"):
                    self._syntax_error("Invalid token syntax", token, self._line)
                (pre, post, token) = self._read_token(token)
                self._flush_buffer(pre, post)
                
                words = token.split()

                if words[0] == "if":
                    # if <variable>
                    if len(words) != 2:
                        self._syntax_error("Don't understand if", token, self._line)
                    self._ops_stack.append(["if", self._line])

                    node = IfNode(self, self._variable(words[1]))
                    self._stack[-1].append(node)
                    self._stack.append(node.get_current())


                elif words[0] == "elif":
                    # elif <condition...>
                    if len(words) != 2:
                        self._syntax_error("Don't understand elif", token, self._line)

                    if not self._ops_stack:
                        self._syntax_error("Mismatched elif", token, self._line)
                    start_what = self._ops_stack[-1]
                    if start_what[0] != "if":
                        self._syntax_error("Mismatched elif", token, self._line)

                    self._stack.pop()
                    node = self._stack[-1][-1]

                    node.add_elif(self._variable(words[1]))
                    self._stack.append(node._get_current())
                
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

                    node.add_else()
                    self._stack.append(node._get_current())

                elif words[0] == "for":
                    # for <variable> in <list>
                    if len(words) != 4 or words[2] != "in":
                        self._syntax_error("Don't understarnd for", token, self._line)
                    self._ops_stack.append(["for", self._line])

                    var1 = self._variable(words[1], False)
                    var2 = self._variable(words[3])

                    node = ForNode(self, var1, var2)
                    self._stack[-1].append(node)
                    self._stack.append(node._actions)

                elif words[0] == "continue":
                    # continue
                    if len(words) != 1:
                        self._syntax_error("Don't understand continue", token, self._line)
                    
                    if not self._ops_stack:
                        self._syntax_error("Mismatched continue", token, self._line)
                    start_what = self._ops_stack[-1]
                    if start_what[0] != "for":
                        self._syntax_error("Mismatched continue", token, self._line)

                    pass

                elif words[0] == "break":
                    # break
                    if len(words) != 1:
                        self._syntax_error("Don't understand break", token, self._line)
                    
                    if not self._ops_stack:
                        self._syntax_error("Mismatched break", token, self._line)
                    start_what = self._ops_stack[-1]
                    if start_what[0] != "for":
                        self._syntax_error("Mismatched break", token, self._line)

                    pass

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
                        pass
                    else:
                        self._stack.pop()
                else:
                    self._syntax_error("Don't understand tag", words[0], self._line)

            else:
                #Literal content
                if token:
                    self._buffer.append(token)

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
                node = TextNode(self, expr)
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

    def _syntax_error(self, msg, thing, where):
        """ Raise an error if something is wrong. """

        if self._filename:
            raise Error("{0} on line {1} file {2}: - {3}".format(msg, where, self._filename, repr(thing)))
        else:
            raise Error("{0} on line {1}: - {2}".format(msg, where, repr(thing)))

    def _variable(self, what, allow_dots=True):
        """ Track a varialbe that is used. """
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
    
    def render(self, renderer, context=None):
        """ Render the template. """
        env = self._env
        env.save_context()
        try:
            if context:
                env._context.update(context)
            for action in self._actions:
                action.render(renderer)
        finally:
            env.restore_context()

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
    import sys
    class OutputRenderer(Renderer):
        def render(self, text):
            sys.stdout.write(text)

    import argparse

    parser = argparse.ArgumentParser(description="Template Test")
    parser.add_argument("-c", dest="code", action="store_true", default=False, help="Output the generated code")
    parser.add_argument("template", help="Location of the template")
    parser.add_argument("data", nargs="?", help="Location of the data json")

    args = parser.parse_args()

    filters = {
    }

    e = Environment(None, filters)
    t = e.load_file(args.template)
    if args.code:
        print(t._code)
    else:
        import json
        data = json.loads(open(args.data).read())
        t.render(OutputRenderer(), data)

        


