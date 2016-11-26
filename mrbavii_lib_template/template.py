""" Represent a single template for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import os

from .errors import *
from .parser import TemplateParser


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

    def __init__(self, env, text=None, filename=None):
        """ Initialize a template with context variables. """
        
        # Initialize
        self._env = env
        self._text = text
        self._filename = filename

        if text is None:
            raise Error("Template text must be specified.")

        self._defines = {}

        # Parse the template
        parser = TemplateParser(self, text)
        self._nodes = parser.parse()

    def render(self, renderer, context=None, retvar=None):
        """ Render the template. """
        env = self._env
        scope = env._push_scope()
        try:
            if not context is None:
                scope._local.update(context)

            self._nodes.render(renderer)
        finally:
            env._pop_scope()

        # Set up any return values:
        if retvar:
            env.set(retvar, scope._template.get(":return:", {}))

