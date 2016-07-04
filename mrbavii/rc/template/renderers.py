# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides the renderers used by the template engine.


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


