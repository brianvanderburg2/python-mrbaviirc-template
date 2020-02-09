""" Handler for the strip action tag. """
# pylint: disable=too-few-public-methods,too-many-arguments,protected-access,unused-argument

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from . import ActionHandler, DefaultActionHandler
from ..tokenizer import Token


class StripActionHandler(ActionHandler):
    """ Handle strip actions. """

    def handle_action_strip(self, line, start, end):
        """ Handle the strip action. """
        parser = self.parser

        if start <= end:
            token = parser.get_expected_token(
                start,
                end,
                Token.TYPE_WORD,
                "Expected on, off, or trim",
                ["on", "off", "trim"]
            )
            start += 1

            if token.value == "on":
                value = parser.AUTOSTRIP_STRIP
            elif token.value == "trim":
                value = parser.AUTOSTRIP_TRIM
            else:
                value = parser.AUTOSTRIP_NONE
        else:
            value = None

        parser.push_autostrip(value)
        parser.push_handler(StripSubHandler(self.parser, self.template))

    def handle_action_autostrip(self, line, start, end):
        """ Handle autostrip """
        self.parser.get_no_more_tokens(start, end)
        self.parser.set_autostrip(self.parser.AUTOSTRIP_STRIP)

    def handle_action_autotrim(self, line, start, end):
        """ Handle autotrim """
        self.parser.get_no_more_tokens(start, end)
        self.parser.set_autostrip(self.parser.AUTOSTRIP_TRIM)

    def handle_action_no_autostrip(self, line, start, end):
        """ Handle no_autostrip """
        self.parser.get_no_more_tokens(start, end)
        self.parser.set_autostrip(self.parser.AUTOSTRIP_NONE)


class StripSubHandler(DefaultActionHandler):
    """ Handle items under strip """

    def handle_action_endstrip(self, line, start, end):
        """ Handle nested action tags """

        self.parser.get_no_more_tokens(start, end)
        self.parser.pop_autostrip()
        self.parser.pop_handler()

    def handle_break(self, line):
        """ Allow break from within a strip block. """
        self.next.handle_break(line)

    def handle_continue(self, line):
        """ Allow continue from within a strip block. """
        self.next.handle_continue(line)


ACTION_HANDLERS = {
    "strip": StripActionHandler,
    "autostrip": StripActionHandler,
    "autotrim": StripActionHandler,
    "no_autostrip": StripActionHandler
}
