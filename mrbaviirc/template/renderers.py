""" Renderers for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "MIT"


class Renderer(object):
    """ A renderer takes content and renders it in some fashion. """

    def __init__(self):
        """ Initialize the renderer. """
        self._sections = {}
        self._cursection = []
        pass

    def render(self, content):
        """ Render the content. """
        if self._cursection:
            section = self._cursection[-1]
            self._sections[section].append(content)
            return True
        else:
            return False

    def push_section(self, name):
        """ Set a named section to render to. """
        self._sections.setdefault(name, [])
        self._cursection.append(name)

    def pop_section(self):
        """ Return rendering to the previous section or default. """
        self._cursection.pop()

    def get_sections(self):
        """ Return all known sections. """
        return list(self._sections.keys())

    def get_section(self, name):
        """ Return the contents of a particular section. """
        if name in self._sections:
            return "".join(self._sections[name])

        return ""


class StreamRenderer(Renderer):
    """ Render to a given stream. """

    def __init__(self, stream):
        """ Initialize the stream. """
        Renderer.__init__(self)
        self._stream = stream

    def render(self, content):
        """ Render to the stream. """
        if not Renderer.render(self, content):
            self._stream.write(content)


class StringRenderer(Renderer):
    """ Render to a string. """

    def __init__(self):
        """ Initialize the renderer. """
        Renderer.__init__(self)
        self._buffer = []

    def render(self, content):
        """ Render the content to the buffer. """
        if not Renderer.render(self, content):
            self._buffer.append(content)

    def get(self):
        """ Get the buffer. """
        return "".join(self._buffer)



