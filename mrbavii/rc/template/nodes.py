# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides the nodes used by the template engine.

from .errors import *


__all__ = [
    "Node", "TextNode", "IfNode", "ForNode", "VarNode", "IncludeNode",
    "WithNode", "AssignNode", "SetNode"
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


