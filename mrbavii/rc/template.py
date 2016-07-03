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

# Errors
################################################################################

class Error(Exception):
    """ Base template engine error. """
    def __init__(self, message):
        self.message = message

class TemplateError(Error):
    """ An error at a specific location in atemplate file. """
    MESSAGE_PREFIX = "Template Error"

    def __init__(self, message, filename, line):
        Error.__init__(self, "{0}: {1} on {2}:{3}".format(
            self.MESSAGE_PREFIX,
            message,
            filename if filename else "<string>",
            line
        ))
        self.filename = filename
        self.line = line

class SyntaxError(TemplateError):
    """ Represent a syntax error in the template. """
    MESSAGE_PREFIX = "Syntax Error"

class UnknownVariableError(TemplateError):
    """ Represent an unknown variable access. """
    MESSAGE_PREFIX = "Unknown Variable Error"

class UnknownFilterError(TemplateError):
    """ Represent an unknown filter access. """
    MESSAGE_PREFIX = "Unknown Filter Error"
    

_KEY_ERRORS = (KeyError, ValueError, TypeError, AttributeError)

# Renderers
################################################################################

class Renderer(object):
    """ A renderer takes content and renders it in some fashion. """

    def __init__(self):
        """ Initialize the renderer. """
        pass

    def render(self, content):
        """ Render the content. """
        raise NotImplementedError


class StreamRenderer(Renderer):
    """ Render to a given stream. """

    def __init__(self, stream):
        """ Initialize the stream. """
        Renderer.__init__(self)
        self._stream = stream

    def render(self, content):
        """ Render to the stream. """
        self._stream.write(content)


class StringRenderer(Renderer):
    """ Render to a string. """

    def __init__(self):
        """ Initialize the renderer. """
        Renderer.__init__(self)
        self._buffer = []

    def render(self, content):
        """ Render the content to the buffer. """
        self._buffer.append(content)

    def get(self):
        """ Get the buffer. """
        return "".join(self._buffer)


# Nodes
################################################################################

class Node(object):
    """ A node is a part of the expression that is rendered. """

    def __init__(self, template, line):
        """ Initialize the node. """
        self._template = template
        self._line = line
        self._env = template._env

    def render(self, renderer):
        """ Render the node to a renderer. """
        raise NotImplementedError


class TextNode(Node):
    """ A node that represents a raw block of text. """

    def __init__(self, template, line, text):
        """ Initialize a text node. """
        Node.__init__(self, template, line)
        self._text = text

    def render(self, renderer):
        """ Render content from a text node. """
        renderer.render(self._text)


class IfNode(Node):
    """ A node that manages if/elif/else. """

    def __init__(self, template, line, expr):
        """ Initialize the if node. """
        Node.__init__(self, template, line)
        self._expr = expr
        self._if = []
        self._else = []

    def render(self, renderer):
        """ Render the if node. """
        try:
            result = self._expr.eval()
        except (UnknownVariableError, UnknownFilterError):
            result = False

        if result:
            for action in self._if:
                action.render(renderer)
        elif self._else:
            for action in self._else:
                action.render(renderer)


class ForNode(Node):
    """ A node for handling for loops. """

    def __init__(self, template, line, var, expr):
        """ Initialize the for node. """
        Node.__init__(self, template, line)
        self._var = var
        self._expr = expr
        self._nodes = []

    def render(self, renderer):
        """ Render the for node. """
        env = self._env

        # Iterate over each value
        values = self._expr.eval()
        if values:
            for var in values:
                env.set(self._var, var)
                                    
                # Execute each sub-node
                for node in self._nodes:
                    node.render(renderer)


class VarNode(Node):
    """ A node to output some value. """

    def __init__(self, template, line, expr):
        """ Initialize the node. """
        Node.__init__(self, template, line)
        self._expr = expr

    def render(self, renderer):
        """ Render the output. """
        renderer.render(str(self._expr.eval()))


class IncludeNode(Node):
    """ A node to include another template. """

    def __init__(self, template, line, filename):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self._filename = filename

    def render(self, renderer):
        """ Actually do the work of including the template. """
        try:
            self._template._include(self._filename, renderer)
        except (IOError, OSError) as e:
            raise TemplateError(
                str(e),
                self._template._filename,
                self._line
            )


class WithNode(Node):
    """ Save the state of the context. """

    def __init__(self, template, line):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._nodes = []

    def render(self, renderer):
        """ Render. """
        self._env.save_context()
        for node in self._nodes:
            node.render(renderer)
        self._env.restore_context()


class AssignNode(Node):
    """ Set a variable to a subvariable. """

    def __init__(self, template, line, var, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._var = var
        self._expr = expr

    def render(self, renderer):
        """ Set the value. """
        self._env.set(self._var, self._expr.eval())


class SetNode(Node):
    """ Set or clear a flag. """

    def __init__(self, template, line, var, value):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._var = var
        self._value = bool(value)

    def render(self, renderer):
        """ Set or clear the value. """
        self._env.set(self._var, self._value)


# Expresssions
################################################################################

class Expr(object):
    """ Base for an expression object. """

    def __init__(self, template, line):
        """ Initialize the expression object. """
        self._template = template
        self._env = template._env
        self._line = line

    def eval(self):
        """ Evaluate the expression object. """
        raise NotImplementedError


class ValueExpr(Expr):
    """ An expression that represents a value. """

    def __init__(self, template, line, value):
        """ Initialize the value expression. """
        Expr.__init__(self, template, line)
        self._value = value

    def eval(self):
        """ Evaluate the expression. """
        return self._value


class FilterExpr(Expr):
    """ An expression that represents a filter to call. """

    def __init__(self, template, line, node, filter, nodes):
        """ Initialize the filter expression. """
        Expr.__init__(self, template, line)
        self._node = node
        self._filter = filter
        self._nodes = nodes

    def eval(self):
        """ Evaluate the expression. """
        value = self._node.eval()

        params = []
        for node in self._nodes:
            params.append(node.eval())

        try:
            return self._env.filter(self._filter, value, *params)
        except KeyError:
            raise UnknownFilterError(
                self._filter,
                self._template._filename,
                self._line
            )

class VarExpr(Expr):
    """ An expression that represents a variable. """

    def __init__(self, template, line, var):
        """ Initialize the variable expression. """
        Expr.__init__(self, template, line)
        self._var = var

    def eval(self):
        """ Evaluate the expression. """
        try:
            return self._env.get(self._var)
        except _KEY_ERRORS:
            raise UnknownVariableError(
                ".".join(self._var),
                self._template._filename,
                self._line
            )

# Parser
################################################################################

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
    
    def _parse_text(self, text):
        """ Parse the template from the text and build the node list. """

        for token in re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text):
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


# Environment and Template
################################################################################

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

    def load_text(self, text):
        """ Load a template from a string. """
        return Template(self, text=text)

    def save_context(self):
        """ Save the current context. """
        self._saved_contexts.append(dict(self._context))

    def restore_context(self):
        """ Restore a saved context. """
        self._context = self._saved_contexts.pop()

    def get(self, var):
        """ Evaluate dotted expressions. """
        value = self._context[var[0]]
        if callable(value):
            value = value()

        for dot in var[1:]:
            value = value[dot]
            if callable(value):
                value = value()
                
        return value

    def set(self, var1, var2):
        """ Set a value in the context. """
        self._context[var1] = var2

    def filter(self, filter, value, *params):
        """ Filter a value. """
        return self._filters[filter](value, *params)


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

    def __init__(self, env, text=None, filename=None):
        """ Initialize a template with context variables. """
        
        # Initialize
        self._env = env
        self._filename = filename

        if text is None:
            if self._filename is None:
                raise Error("Filename must be specified if text is not.")
            text = open(self._filename, "rU").read()

        # Parse the template
        parser = TemplateParser(self, text)
        self._nodes = parser.parse()

    def render(self, renderer, context=None):
        """ Render the template. """
        env = self._env
        env.save_context()
        try:
            if context:
                env._context.update(context)
            for node in self._nodes:
                node.render(renderer)
        finally:
            env.restore_context()

    def _include(self, filename, renderer):
        """ Include another template. """
        if self._filename is None:
            raise Error("Can't include a template if a filename isn't specified.")

        newfile = os.path.join(os.path.dirname(self._filename), *(filename.split("/")))
        t = self._env.load_file(newfile)
        t.render(renderer)



# Test
################################################################################

if __name__ == "__main__":
    try:
        import sys
        import argparse
        
        import json

        parser = argparse.ArgumentParser(description="Template Test")
        parser.add_argument("-c", dest="count", default=1, help="Render the template this many times")
        parser.add_argument("template", help="Location of the template")
        parser.add_argument("data", nargs="?", help="Location of the data json")

        args = parser.parse_args()

        filters = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "equal": lambda x, y: x == y,
            "odd": lambda x: x % 2 == 1,
            "even": lambda x: x % 2 == 0
        }

        e = Environment(None, filters)
        t = e.load_file(args.template)

        data = json.loads(open(args.data, "rU").read())
        o = StreamRenderer(sys.stdout)

        for i in range(int(args.count)):
            data["cycle"] = i + 1
            t.render(o, data)
    except Error as e:
        print(e.message)

        


