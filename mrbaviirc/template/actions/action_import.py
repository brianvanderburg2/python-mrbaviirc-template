""" Handler for the import action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..errors import UnknownImportError
from ..nodes import Node


class ImportNode(Node):
    """ Import a library to a variable in the current scope. """
    def __init__(self, template, line, assigns):
        Node.__init__(self, template, line)
        self.assigns = assigns

    def render(self, renderer, scope):
        """ Do the import. """
        env = self.env

        for (var, expr) in self.assigns:
            name = expr.eval(scope)
            try:
                imp = env.load_import(name)
                scope.set(var, imp)
            except KeyError:
                raise UnknownImportError(
                    "No such import: {0}".format(name),
                    self.template.filename,
                    self.line
                )


def import_handler(parser, template, line, action, start, end):
    """ Parse the action """
    assigns = parser._parse_multi_assign(start, end)

    node = ImportNode(template, line, assigns)
    parser.add_node(node)


ACTION_HANDLERS = {"import": import_handler}
