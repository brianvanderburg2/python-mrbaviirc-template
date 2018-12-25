""" Represent a single template for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import os
import threading

from .errors import *
from .parser import TemplateParser
from .scope import Scope


class Template(object):
    """ Simple template parser and renderer.

    Extended variable access:

        {{ expression }}

        For example:

            {{ value.subvalue }}

            {{ value.subvalue | upper }}


    Loops:

        {% for var in list %}
        {% endfor %}

    Conditions:

        {% if var %}
        {% elif var %}
        {% else %}
        {% endif %}

    Comments:

        {# This is a commend. #}

    Whitespace control.  A "-" after an opening block will eat any preceeding
    whitespace up to and including the previous new line:

        {#- ... #}
        {{- ... }}
        {%- ... %}
    """

    def __init__(self, env, text, filename, allow_code=False):
        """ Initialize a template with context variables. """
        
        # Initialize
        self._env = env
        self._text = text
        self._filename = filename
        self._allow_code = allow_code

        self._private = {}
        self._lock = threading.Lock()

        # Parse the template
        parser = TemplateParser(self, text)
        self._nodes = parser.parse()

    def render(self, renderer, context=None):
        """ Render the template. """

        # Create the top (global) scope for this render
        scope = Scope()
        if context is not None:
            scope.update(context)

        return self._render(renderer, None, scope)

    def _render(self, renderer, context, scope):
        """ Render the template. """
        new_scope = scope.push(True)

        if context is not None:
            new_scope.update(context)

        # set certain variables
        new_scope._template["__filename__"] = self._filename

        self._nodes.render(renderer, new_scope)

        # Return any template return values:
        retval = new_scope._template.get(":return:", {})
        return retval

