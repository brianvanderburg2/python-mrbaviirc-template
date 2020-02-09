""" Renderers for the template engine. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


class Renderer:
    """ A renderer takes content and renders it in some fashion. """

    def __init__(self):
        """ Initialize the renderer. """
        self._captures = []
        self._captures_stack = []

    def render(self, content):
        """ Render the content. """
        if self._captures:
            self._captures[-1].append(content)
        else:
            self.do_render(content)

    def start_capture(self):
        """ Start capturing rendered content. """
        self._captures.append([])

    def get_capture(self):
        """ Get the captured rendered content. """
        return "".join(self._captures[-1])

    def stop_capture(self):
        """ Stop capturing rendered content. """
        return self._captures.pop()

    def save_captures(self):
        """ Save the current captures stack (not the contents). """
        self._captures_stack.append(list(self._captures))

    def restore_captures(self):
        """ Restore the current captures statck (not the contents). """
        self._captures = self._captures_stack.pop()


class StreamRenderer(Renderer):
    """ Render to a given stream. """

    def __init__(self, stream):
        """ Initialize the stream. """
        Renderer.__init__(self)
        self.stream = stream

    def do_render(self, content):
        """ Render to the stream. """
        self.stream.write(content)


class StringRenderer(Renderer):
    """ Render to a string. """

    def __init__(self):
        """ Initialize the renderer. """
        Renderer.__init__(self)
        self.buffer = []

    def do_render(self, content):
        """ Render the content to the buffer. """
        self.buffer.append(content)

    def get(self):
        """ Get the buffer. """
        return "".join(self.buffer)
