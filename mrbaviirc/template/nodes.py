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

    def __init__(self, template, line, target):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self._target = target

    def render(self, renderer):
        """ Actually do the work of including the template. """
        self._target.render(renderer, save=False)


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


