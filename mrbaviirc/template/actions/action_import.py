""" Handler for the import action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..errors import UnknownImportError
from ..nodes import Node


class ImportNode(Node):
    """ Import a library to a variable in the template. """
    def __init__(self, template, line, assigns):
        Node.__init__(self, template, line)
        self.assigns = assigns

    def render(self, state):
        """ Do the import. """
        env = self.env

        for (var, expr) in self.assigns:
            name = expr.eval(state)
            try:
                imp = env.load_import(name)
                state.set_var(var[0], imp, var[1])
            except KeyError:
                raise UnknownImportError(
                    "No such import: {0}".format(name),
                    self.template.filename,
                    self.line
                )


class ImportActionHandler(ActionHandler):
    """ Handle import """

    def handle_action_import(self, line, start, end):
        """ Handle import """
        assigns = self.parser._parse_multi_assign(start, end, allow_type=True)

        node = ImportNode(self.template, line, assigns)
        self.parser.add_node(node)


ACTION_HANDLERS = {"import": ImportActionHandler}
