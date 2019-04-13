""" Represent a single template for the template engine. """

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"


import threading

from .parser import TemplateParser
from .scope import Scope
from .lib.builtin import context as builtin_context


class Template(object):
    """ Main template object hold the nodes of the parsed template. """

    def __init__(self, env, text, filename, allow_code=False):
        """ Initialize a template with context variables. """

        # Initialize
        self.env = env
        self.text = text
        self.filename = filename
        self.code_enabled = allow_code

        self.private = {}
        self.lock = threading.Lock()

        # Parse the template
        parser = TemplateParser(self, text)
        self.nodes = parser.parse()

    def render(self, renderer, context=None, userdata=None, abort_fn=None):
        """ Render the template. """

        # Create the top (global) scope for this render
        scope = Scope(userdata=userdata, abort_fn=abort_fn)

        scope.update(builtin_context) # Add builtin only
        if context is not None:
            scope.update(context)

        return self.nested_render(renderer, None, scope)

    def nested_render(self, renderer, context, scope):
        """ Render the template. """
        new_scope = scope.push(True)

        if context is not None:
            new_scope.update(context)

        # set certain variables
        new_scope.template_scope["__filename__"] = self.filename

        self.nodes.render(renderer, new_scope)

        # Return any template return values:
        retval = new_scope.template_scope.get(":return:", {})
        return retval
