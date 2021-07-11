""" Renderers for the template engine. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


class Renderer:
    """ A renderer takes content and renders it in some fashion. """

    def __init__(self):
        """ Initialize the renderer. """
        pass

    def render(self, content):
        """ Render the content. """
        raise NotImplementedError("Not yet implemented")

class StreamRenderer(Renderer):
    """ Render to a given stream. """

    def __init__(self, stream):
        """ Initialize the stream. """
        Renderer.__init__(self)
        self.stream = stream

    def render(self, content):
        """ Render to the stream. """
        self.stream.write(content)


class StringRenderer(Renderer):
    """ Render to a string. """

    def __init__(self):
        """ Initialize the renderer. """
        Renderer.__init__(self)
        self.buffer = []

    def render(self, content):
        """ Render the content to the buffer. """
        self.buffer.append(content)

    def get(self):
        """ Get the buffer. """
        return "".join(self.buffer)
