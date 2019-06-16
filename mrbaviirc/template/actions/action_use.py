""" Handler for the use action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node


class UseSectionNode(Node):
    """ A node to use a section in the output. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, renderer, scope):
        """ Render the section to the output. """

        section = str(self.expr.eval(scope))
        renderer.render(renderer.get_section(section))


def use_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = parser._parse_expr(start, end)

    node = UseSectionNode(template, line, expr)
    parser.add_node(node)


ACTION_HANDLERS = {"use": use_handler}
