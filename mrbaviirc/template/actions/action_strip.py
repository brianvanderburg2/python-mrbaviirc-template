""" Handler for the strip action tag. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016-2019"
__license__ = "Apache License 2.0"


from ..tokenizer import Token


def strip_handler(parser, template, line, action, start, end):
    """ Parse the action """
    if start <= end:
        token = parser._get_expected_token(
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
    parser.push_handler(strip_subhandler)


def strip_subhandler(parser, template, line, action, start, end):
    """ Handle nested action tags """
    
    if action == "endstrip":
        parser._get_no_more_tokens(start, end)
        parser.pop_autostrip()
        parser.pop_handler()

    else:
        parser.handle_action(parser, template, line, action, start, end)


def autostrip_handler(parser, template, line, action, start, end):
    """ Parse the action. """
    parser._get_no_more_tokens(start, end)
    parser.set_autostrip(parser.AUTOSTRIP_STRIP)


def autotrim_handler(parser, template, line, action, start, end):
    """ Parse the action. """
    parser._get_no_more_tokens(start, end)
    parser.set_autostrip(parser.AUTOSTRIP_TRIM)

def noautostrip_handler(parser, template, line, action, start, end):
    """ Parse the action. """
    parser._get_no_more_tokens(start, end)
    parser.set_autostrip(parser.AUTOSTRIP_NONE)


ACTION_HANDLERS = {
    "strip": strip_handler,
    "autostrip": autostrip_handler,
    "autotrim": autotrim_handler,
    "no_autostrip": noautostrip_handler
}
