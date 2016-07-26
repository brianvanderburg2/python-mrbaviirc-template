# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides the template used by the template engine.

import os

from .errors import *
from .parser import TemplateParser
from ..codebuild import CodeBuilder

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
        self._filename = filename

        if text is None:
            if self._filename is None:
                raise Error("Filename must be specified if text is not.")
            text = open(self._filename, "rU").read()

        self._defines = {}

        # Parse the template
        parser = TemplateParser(self, text)
        self._nodes = parser.parse()

    def render(self, renderer, context=None, save=True):
        """ Render the template. """
        env = self._env
        if save:
            env.save_context()

        if context:
            env._context.update(context)

        for node in self._nodes:
            node.render(renderer)

        if save:
            env.restore_context()

    def _include(self, filename):
        """ Include another template. """
        if self._filename is None:
            raise Error("Can't include a template if a filename isn't specified.")

        newfile = os.path.join(os.path.dirname(self._filename), *(filename.split("/")))
        return self._env.load_file(newfile)

