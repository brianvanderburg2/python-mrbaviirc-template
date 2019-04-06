""" Handler for the switch action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..nodes import SwitchNode
from ..errors import SyntaxError


def switch_handler(parser, template, line, action, start, end):
    """ Parse the action """
    expr = parser._parse_expr(start, end)

    node = SwitchNode(template, line, expr)
    parser.add_node(node)
    parser.push_nodestack(node.nodes)
    parser.push_handler(switch_subhandler)

def switch_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """

    if action in SwitchNode.types:
        offset = SwitchNode.types.index(action)
        argc = SwitchNode.argc[offset]

        exprs = parser._parse_multi_expr(start, end)

        if len(exprs) != argc:
            raise SyntaxError(
                "Switch clause {0} takes {1} argument".format(action, argc),
                template.filename,
                line
            )

        node = parser.pop_nodestack()
        node.add_case(SwitchNode.cbs[offset], exprs)
        parser.push_nodestack(node.nodes)

    elif action == "endswitch":
        parser._get_no_more_tokens(start, end)
        parser.pop_nodestack()
        parser.pop_handler()

    else:
        parser.handle_action(parser, template, line, action, start, end)


ACTION_HANDLERS = {"switch": switch_handler}
