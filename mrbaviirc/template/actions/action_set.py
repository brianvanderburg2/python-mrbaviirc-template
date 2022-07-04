""" Handler for the set action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument
# pylint: disable=missing-docstring

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler
from ..nodes import Node
from ..errors import Error
from ..tokenizer import Token


class AssignNode(Node):
    """ Set a variable to a subvariable. """

    def __init__(self, template, line, assigns, elses):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns
        self.elses = elses

    def render(self, state):
        """ Set the value. """

        # An exception from assigns only passes up if there are no
        # thens and no elses expressions

        try:
            for (var, expr) in self.assigns:
                state.set_var(var[0], expr.eval(state), var[1])
        except Error as e:
            # An expression error occurred, run elses or reraise error
            if self.elses is not None:
                for (var, expr) in self.elses:
                    state.set_var(var[0], expr.eval(state), var[1])
            else:
                raise


class SetActionHandler(ActionHandler):
    """ Handle set """

    def handle_action_set(self, line, start, end):
        """ Handle set. """

        parser = self.parser
        segments = parser.find_tag_segments(start, end)
        assigns = None
        elses = None

        # Normal assignments are first
        if len(segments) > 0:
            (start, end) = segments[0]
            assigns = self.parser.parse_multi_assign(start, end, allow_type=True)

        # Find then/else assignments
        for segment in segments[1:]:
            (start, end) = segment

            token = parser.get_expected_token(
                start,
                end,
                Token.TYPE_WORD,
                values=["else"]
            )
            start += 1

            if token.value == "else":
                elses = parser.parse_multi_assign(start, end, allow_type=True)
                continue

        if assigns is None:
            raise ParserError(
                "Set expecting expressions",
                self.template.filename,
                line
            )

        node = AssignNode(self.template, line, assigns, elses)
        self.parser.add_node(node)


ACTION_HANDLERS = {
    "set": SetActionHandler,
}
