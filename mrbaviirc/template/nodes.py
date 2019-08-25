""" Provide the nodes for the template engine. """
# pylint: disable=too-few-public-methods,too-many-arguments

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"

__all__ = ["Node", "NodeList", "TextNode", "EmitNode"]


import weakref

from .errors import AbortError


class Node(object):
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
        return self._env()

    @property
    def template(self):
        return self._template()

    def render(self, renderer, scope):
        """ Render the node to a renderer.
            If a value is returned other than None, then for most other
            nodes it should return that value instantly.  Certain nodes
            may use the value in a special manor, such as break and
            continue nodes.
        """
        raise NotImplementedError


class NodeList(object):
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

    def render(self, renderer, scope):
        """ Render all nodes. """
        if scope.abort_fn and scope.abort_fn():
            raise AbortError("Nodelist render aborted")

        for node in self.nodes:
            result = node.render(renderer, scope)
            if result in (Node.RENDER_BREAK, Node.RENDER_CONTINUE):
                return result

    def __getitem__(self, index):
        return self.nodes[index]


class TextNode(Node):
    """ A node that represents a raw block of text. """

    def __init__(self, template, line, text):
        """ Initialize a text node. """
        Node.__init__(self, template, line)
        self.text = text

    def render(self, renderer, scope):
        """ Render content from a text node. """
        renderer.render(self.text)


class EmitNode(Node):
    """ A node to output some value. """

    def __init__(self, template, line, expr):
        """ Initialize the node. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, renderer, scope):
        """ Render the output. """
        renderer.render(str(self.expr.eval(scope)))
