""" Provide access to all the action tags. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2019"
__license__ = "Apache License 2.0"

__all__ = ["ACTION_HANDLERS"]


from ..nodes import Node, TextNode, EmitNode
from ..expr import ValueExpr
from ..errors import ParserError


class ActionHandler:
    """ Handle evens when the parser encounters tags, text, and so on. """

    def __init__(self, parser, template):
        """ Initialize the handler. """

        self.parser = parser
        self.template = template

        self.line = 1 # current tag line when when calling parser.push_handler

    def handle_text(self, line, text):
        """ Add a  text node. """
        node = TextNode(self.template, line, text)
        self.parser.add_node(node)

    def handle_emitter(self, line, start, end):
        """ Add an emitter node. """
        expr = self.parser.parse_expr(start, end)
        line = self.parser.tokens[start].line

        if isinstance(expr, ValueExpr):
            node = TextNode(self.template, line, str(expr.eval(None)))
        else:
            node = EmitNode(self.template, line, expr)

        self.parser.add_node(node)

    def handle_comment(self, line):
        """ Allow for controlling whether a tag can contain comments. """
        pass

    def handle_action(self, line, action, start, end):
        """ Handle action tags. """
        handler = getattr(self, "handle_action_" + action, None)
        if handler:
            handler(line, start, end)
        else:
            self.handle_unknown_action(line, action, start, end)

    def handle_unknown_action(self, line, action, start, end):
        """ Handle other action tags. """
        raise ParserError(
            "Unknown action tag: " + action,
            self.template.filename,
            line
        )


class DefaultActionHandler(ActionHandler):
    """ Handle the default action tags. """

    def handle_unknown_action(self, line, action, start, end):
        if action in ACTION_HANDLERS:
            handler = ACTION_HANDLERS[action](self.parser, self.template)
            handler.handle_action(line, action, start, end)
        else:
            raise ParserError(
                "Unknown action tag: " + action,
                self.template.filename,
                line
            )


# Import submodules
def _import_actions():
    import pkgutil
    import importlib

    actions = {}
    for (_, name, _) in pkgutil.iter_modules(__path__):
        pkg_name = __package__ + "." + name
        module = importlib.import_module(pkg_name)

        module_actions = getattr(module, "ACTION_HANDLERS", None)
        if module_actions is None:
            continue

        for (action_name, action_handler) in module_actions.items():
            assert action_name not in actions, "Duplicate Action {0}".format(action_name)
            actions[action_name] = action_handler

    return actions


# Load them
ACTION_HANDLERS = _import_actions()
del _import_actions
