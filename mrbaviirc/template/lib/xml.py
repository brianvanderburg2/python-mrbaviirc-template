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

    def attr_tag(self):
        return self._node.tag

    def attr_ns(self):
        return self._ns

    def attr_tagname(self):
        return self._tagname

    def attr_text(self):
        return self._node.text if self._node.text else ""

    def attr_tail(self):
        return self._node.tail if self._node.tail else ""

    def attr_alltext(self):
        return "".join(self._node.itertext())

    def func_attr(self, name, defval=None):
        return self._node.attrib.get(name, defval)

    def __iter__(self):
        for child in self._node:
            yield ElementTreeWrapper(child)

    def func_findall(self, path):
        for child in self._node.findall(path):
            yield ElementTreeWrapper(child)

    def func_find(self, path):
        child = self._node.find(path)
        if not child is None:
            child = ElementTreeWrapper(child)

        return child

    def func_str(self):
        return ET.tostring(self._node)


