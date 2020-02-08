""" Provide the nodes for the template engine. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"

__all__ = [
    "Node", "NodeList", "TextNode", "EmitNode", "BreakNode", "ContinueNode"
]


import weakref

from .errors import AbortError


class Node:
    """ A node is a part of the expression that is rendered. """

    RENDER_BREAK = 1
    RENDER_CONTINUE = 2

    def __init__(self, template, line):
        """ Initialize the node. """
        self._template = weakref.ref(template)
        self.line = line
        self._env = weakref.ref(template.env)

    @property
    def env(self):
        """ Return the environment object or None """
        return self._env()

    @property
    def template(self):
        """ Return the template object or None """
        return self._template()

    def render(self, state):
        """ Render the node to a renderer.
            If a value is returned other than None, then for most other
            nodes it should return that value instantly.  Certain nodes
            may use the value in a special manor, such as break and
            continue nodes.
        """
        raise NotImplementedError


class NodeList:
    """ A list of nodes. """

    def __init__(self):
        """Initialize. """
        self.nodes = []

    def append(self, node):
        """ Append a node to the list. """
        self.nodes.append(node)

    def extend(self, nodelist):
        """ Extend one node list with another. """
        self.nodes.extend(nodelist.nodes)

    def render(self, state):
        """ Render all nodes. """
        if state.abort_fn and state.abort_fn():
            raise AbortError("Nodelist render aborted")

        for node in self.nodes:
            result = node.render(state)
            if result in (Node.RENDER_BREAK, Node.RENDER_CONTINUE):
                return result

        return None

    def __getitem__(self, index):
        return self.nodes[index]


class TextNode(Node):
    """ A node that represents a raw block of text. """

    def __init__(self, template, line, text):
        """ Initialize a text node. """
        Node.__init__(self, template, line)
        self.text = text

    def render(self, state):
        """ Render content from a text node. """
        state.renderer.render(self.text)


class EmitNode(Node):
    """ A node to output some value. """

    def __init__(self, template, line, expr):
        """ Initialize the node. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, state):
        """ Render the output. """
        state.renderer.render(str(self.expr.eval(state)))


class BreakNode(Node):
    """ Return RENDER_BREAK. """

    def render(self, state):
        return Node.RENDER_BREAK


class ContinueNode(Node):
    """ Return RENDER_CONTINUE. """

    def render(self, state):
        return Node.RENDER_CONTINUE
