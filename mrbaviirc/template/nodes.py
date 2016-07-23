# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides the nodes used by the template engine.

from .errors import *


__all__ = [
    "Node", "TextNode", "IfNode", "ForNode", "VarNode", "IncludeNode",
    "WithNode", "AssignNode", "SectionNode", "UseSectionNode"
]


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

    def compile(self, code, depth):
        """ Compile the node. """
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

    def compile(self, code, depth):
        """ Compile the node. """
        code.add_line("renderer.render({0})".format(repr(self._text)))


class IfNode(Node):
    """ A node that manages if/elif/else. """

    def __init__(self, template, line, expr):
        """ Initialize the if node. """
        Node.__init__(self, template, line)
        self._ifs = [(expr, [])]
        self._else = None
        self._nodes = self._ifs[0][1]

    def add_elif(self, expr):
        """ Add an if section. """
        # TODO: error if self._else exists
        self._ifs.append((expr, []))
        self._nodes = self._ifs[-1][1]

    def add_else(self):
        """ Add an else. """
        self._else = []
        self._nodes = self._else

    def render(self, renderer):
        """ Render the if node. """
        for (expr, nodes) in self._ifs:
            result = expr.eval()
            if result:
                for node in nodes:
                    node.render(renderer)
                return

        if self._else:
            for node in self._else:
                node.render(renderer)

    def compile(self, code, depth):
        """ Compile the node. """

        first = True
        for (expr, nodes) in self._ifs:
            cexpr = expr.compile()
            if first:
                code.add_line("if {0}:".format(cexpr))
                first = False
            else:
                code.add_line("elif {0}".format(cexpr))

            code.indent()

            for node in nodes:
                node.compile(code, depth + 1)

            code.add_line("pass")
            code.dedent()

        if self._else:
            code.add_line("else:")
            code.indent()

            for node in self._else:
                node.compile(code, depth + 1)

            code.add_line("pass")
            code.dedent()


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

    def compile(self, code, depth):
        """ Compile the node. """

        cexpr = self._expr.compile()
        code.add_line("for f_{0} in {1}:".format(depth, cexpr))
        code.indent()

        code.add_line("env.set({0}, f_{1})".format(repr(self._var), depth))

        for node in self._nodes:
            node.compile(code, depth + 1)

        code.dedent()


class VarNode(Node):
    """ A node to output some value. """

    def __init__(self, template, line, expr):
        """ Initialize the node. """
        Node.__init__(self, template, line)
        self._expr = expr

    def render(self, renderer):
        """ Render the output. """
        renderer.render(str(self._expr.eval()))

    def compile(self, code, depth):
        """ Compile the node. """

        cexpr = self._expr.compile()
        code.add_line("renderer.render(str({0}))".format(cexpr))


class IncludeNode(Node):
    """ A node to include another template. """

    def __init__(self, template, line, target):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self._target = target

    def render(self, renderer):
        """ Actually do the work of including the template. """
        self._target.render(renderer, save=False)

    def compile(self, code, depth):
        """ Compile the node. """
        code.add_line("template = env.load_file({0})".format(repr(self._target._filename)))
        code.add_line("template.render(renderer, save=False, compiled=True)")


class WithNode(Node):
    """ Save the state of the context. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._assigns = assigns
        self._nodes = []

    def render(self, renderer):
        """ Render. """
        env = self._env
        env.save_context()

        for (var, expr) in self._assigns:
            env.set(var, expr.eval())

        for node in self._nodes:
            node.render(renderer)

        env.restore_context()

    def compile(self, code, depth):
        """ Compile the node. """

        code.add_line("env.save_context()")

        for (var, expr) in self._assigns:
            cexpr = expr.compile()
            code.add_line("env.set({0}, {1})".format(repr(var), cexpr))

        for node in self._nodes:
            node.compile(code, depth + 1)

        code.add_line("env.restore_context()")


class AssignNode(Node):
    """ Set a variable to a subvariable. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._assigns = assigns

    def render(self, renderer):
        """ Set the value. """
        env = self._env

        for (var, expr) in self._assigns:
            env.set(var, expr.eval())

    def compile(self, code, depth):
        """ Compile the node. """

        for (var, expr) in self._assigns:
            cexpr = expr.compile()
            code.add_line("env.set({0}, {1})".format(repr(var), cexpr))


class SectionNode(Node):
    """ A node to redirect template output to a section. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._expr = expr
        self._nodes = []

    def render(self, renderer):
        """ Redirect output to a section. """

        section = str(self._expr.eval())
        renderer.push_section(section)

        for node in self._nodes:
            node.render(renderer)

        renderer.pop_section()

    def compile(self, code, depth):
        """ Compile the node. """

        cexpr = self._expr.compile()
        code.add_line("renderer.push_section(str({0}))".format(cexpr))

        for node in self._nodes:
            node.compile(code, depth + 1)

        code.add_line("renderer.pop_section()")


class UseSectionNode(Node):
    """ A node to use a section in the output. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._expr = expr

    def render(self, renderer):
        """ Render the section to the output. """

        section = str(self._expr.eval())
        renderer.render(renderer.get_section(section))

    def compile(self, code, depth):
        """ Compile the node. """

        cexpr = self._expr.compile()
        code.add_line("renderer.render(renderer.get_section(str({0})))".format(cexpr))


