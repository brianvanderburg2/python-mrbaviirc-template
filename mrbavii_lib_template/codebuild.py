""" Provide a container for building code segments. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


class CodeBuilder(object):
    """ A code builder class. """

    INDENT = 4

    def __init__(self, indent=0):
        """ Initialize the bulder with a given indentation level. """
        self._indent = indent
        self._blocks = []

    def add_line(self, line):
        """ Add a line to the builder. """
        self._blocks.extend([" " * self._indent, line, "\n"])

    def indent(self):
        """ Increase the indentation level. """
        self._indent += self.INDENT

    def dedent(self):
        """ Decrease the indentation level. """
        self._indent -= self.INDENT

    def add_section(self):
        """ Add a section that can be filled in later. """
        section = CodeBuilder(self._indent)
        self._blocks.append(section)
        return section

    def __str__(self):
        """ Return the current code. """
        return "".join(str(i) for i in self._blocks)

    def execute(self):
        """ Execute the code and return the globals dictionary. """
        _globals = {}
        exec(str(self), _globals)
        return _globals

