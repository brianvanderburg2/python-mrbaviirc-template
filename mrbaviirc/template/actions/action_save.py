""" Handler for the save action tag. """
# pylint: disable=too-few-public-methods, too-many-arguments, protected-access, unused-argument
# pylint: disable=exec-used

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler, DefaultActionHandler
from ..nodes import Node, NodeList
from ..tokenizer import Token
from ..errors import ParserError, TemplateError
from ..expr import VarExpr


class SaveNode(Node):
    """ A node to execute python code. """

    def __init__(self, template, line, saves):
        """ Initialize the save node. """
        Node.__init__(self, template, line)
        self.saves = tuple(saves)
        self.nodes = NodeList()

    def render(self, state):
        """ Save the variables, handle child nodes, restore the variables. """

        # Save the variables
        saved = []
        for i in self.saves:
            try:
                saved.append((
                    i[0],
                    i[1],
                    state.get_var(i[0], i[1])
                ))
            except KeyError:
                raise UnknownVariableError(
                    i,
                    self.template.filename,
                    self.line
                )

        # Render and restore
        try:
            return self.nodes.render(state)
        finally:
            for (var, where, value) in saved:
                state.set_var(var, value, where)

        
class SaveSubHandler(DefaultActionHandler):
    """ Handler for the save tag internals. """

    def handle_action_endsave(self, line, start, end):
        """ Handle end code. """
        self.parser.get_no_more_tokens(start, end)
        self.parser.pop_nodestack()
        self.parser.pop_handler()


class SaveActionHandler(ActionHandler):
    """ Handler for code tag. """

    def handle_action_save(self, line, start, end):
        """ Handler for code tag. """
        parser = self.parser

        saves = parser.parse_multi_var(start, end, True)
        node = SaveNode(self.template, line, saves)
        parser.add_node(node)
        parser.push_nodestack(node.nodes)
        parser.push_handler(SaveSubHandler(self.parser, self.template))


ACTION_HANDLERS = {"save": SaveActionHandler}
