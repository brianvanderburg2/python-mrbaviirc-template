""" Handler for the break and continue action tags. """
# pylint: disable=too-few-public-methods, too-many-arguments, protected-access, unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import Node


class BreakNode(Node):
    """ Return RENDER_BREAK. """

    def render(self, renderer, scope):
        return Node.RENDER_BREAK


class ContinueNode(Node):
    """ Return RENDER_CONTINUE. """

    def render(self, renderer, scope):
        return Node.RENDER_CONTINUE


def break_handler(parser, template, line, action, start, end):
    """ Parse the action """
    parser._get_no_more_tokens(start, end)

    node = BreakNode(template, line)
    parser.add_node(node)


def continue_handler(parser, template, line, action, start, end):
    """ Parse the action """
    parser._get_no_more_tokens(start, end)

    node = ContinueNode(template, line)
    parser.add_node(node)


ACTION_HANDLERS = {"break": break_handler, "continue": continue_handler}
