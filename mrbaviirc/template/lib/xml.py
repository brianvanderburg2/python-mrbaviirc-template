""" XML related template library. """

from __future__ import absolute_import

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

__all__ = []

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


__all__.append("ElementTreeWrapper")
class ElementTreeWrapper(object):
    """ Class to wrap an XML node for the template engine. """

    def __init__(self, node):
        """ Init the wrapper. """
        self._node = node

        tag = node.tag

        if tag[0] == "{":
            end = tag.find("}")
            if end < 0:
                pass # TODO: error

            ns = tag[1:end]
            tag = tag[end + 1:]
        else:
            ns = ""

        self._ns = ns
        self._tagname = tag

    def __bool__(self):
        return True

    @property
    def tag(self):
        return self._node.tag

    @property
    def ns(self):
        return self._ns

    @property
    def tagname(self):
        return self._tagname

    @property
    def text(self):
        return self._node.text if self._node.text else ""

    @property
    def tail(self):
        return self._node.tail if self._node.tail else ""

    @property
    def alltext(self):
        return "".join(self._node.itertext())

    def attr(self, name, defval=None):
        return self._node.attrib.get(name, defval)

    def __iter__(self):
        for child in self._node:
            yield ElementTreeWrapper(child)

    def findall(self, path):
        for child in self._node.findall(path):
            yield ElementTreeWrapper(child)

    def find(self, path):
        child = self._node.find(path)
        if not child is None:
            child = ElementTreeWrapper(child)

        return child

    def str(self):
        return ET.tostring(self._node, encoding="unicode")


