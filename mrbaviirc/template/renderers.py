""" Renderers for the template engine. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


class Renderer(object):
    """ A renderer takes content and renders it in some fashion. """

    def __init__(self):
        """ Initialize the renderer. """
        self.sections = {}
        self.cursection = []

    def render(self, content):
        """ Render the content. """
        if self.cursection:
            section = self.cursection[-1]
            self.sections[section].append(content)
            return True
        else:
            return False

    def push_section(self, name):
        """ Set a named section to render to. """
        self.sections.setdefault(name, [])
        self.cursection.append(name)

    def pop_section(self):
        """ Return rendering to the previous section or default. """
        self.cursection.pop()

    def get_sections(self):
        """ Return all known sections. """
        return list(self.sections.keys())

    def get_section(self, name):
        """ Return the contents of a particular section. """
        if name in self.sections:
            return "".join(self.sections[name])

        return ""


class StreamRenderer(Renderer):
    """ Render to a given stream. """

    def __init__(self, stream):
        """ Initialize the stream. """
        Renderer.__init__(self)
        self.stream = stream

    def render(self, content):
        """ Render to the stream. """
        if not Renderer.render(self, content):
            self.stream.write(content)


class StringRenderer(Renderer):
    """ Render to a string. """

    def __init__(self):
        """ Initialize the renderer. """
        Renderer.__init__(self)
        self.buffer = []

    def render(self, content):
        """ Render the content to the buffer. """
        if not Renderer.render(self, content):
            self.buffer.append(content)

    def get(self):
        """ Get the buffer. """
        return "".join(self.buffer)
