""" Handler for the set action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node
from ..scope import Scope


class AssignNode(Node):
    """ Set a variable to a subvariable. """

    def __init__(self, template, line, assigns, where):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns
        self.where = where

    def render(self, renderer, scope):
        """ Set the value. """
        for (var, expr) in self.assigns:
            scope.set(var, expr.eval(scope), self.where)


def _set_handler(parser, template, line, action, start, end, where):
    """ Parse the action """
    assigns = parser._parse_multi_assign(start, end)

    node = AssignNode(template, line, assigns, where)
    parser.add_node(node)


def set_handler(parser, template, line, action, start, end):
    return _set_handler(parser, template, line, action, start, end, Scope.SCOPE_LOCAL)


def global_handler(parser, template, line, action, start, end):
    return _set_handler(parser, template, line, action, start, end, Scope.SCOPE_GLOBAL)


def template_handler(parser, template, line, action, start, end):
    return _set_handler(parser, template, line, action, start, end, Scope.SCOPE_TEMPLATE)


def private_handler(parser, template, line, action, start, end):
    return _set_handler(parser, template, line, action, start, end, Scope.SCOPE_PRIVATE)


ACTION_HANDLERS = {
    "set": set_handler,
    "global": global_handler,
    "template": template_handler,
    "private": private_handler
}
