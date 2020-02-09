""" Handler for the use action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node


class UseSectionNode(Node):
    """ A node to use a section in the output. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, state):
        """ Render the section to the output. """

        section = str(self.expr.eval(state))
        state.renderer.render(
            "".join(state.sections.get(section, []))
        )


class UseActionHandler(ActionHandler):
    """ Handle the use action """

    def handle_action_use(self, line, start, end):
        """ Handle use """
        expr = self.parser.parse_expr(start, end)

        node = UseSectionNode(self.template, line, expr)
        self.parser.add_node(node)


ACTION_HANDLERS = {"use": UseActionHandler}
