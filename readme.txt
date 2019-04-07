mrbaviirc.template
==================

A small template system for python

Copyright
=========
Copyright 2012-2019 Brian Allen Vanderburg II

License
=======
This code is licensed under the Apache License 2.0

Security Notice
===============

This library does not attempt to be secure. It is up to the user to ensure they
trust the templates.  Even through the code tag can be disabled, it is still
possible to access other items that could be dangerous if untrusted as below.
While we could restrict access to attributes that start/end with underscores,
right now that is not planned and ever if it were, there would likely be other
ways to gain access to the variables needed

    {% set subclasses = [].__class__.__base__.__subclasses__() %}
    {% for class in subclasses %}
        {% if class.__name__ == "catch_warnings" %}
            {% set builtins = class()._module.__builtins__ %}
    {% endif %}
    {% endfor %}

    {{ builtins["open"]("/etc/passwd", "rt").read() }}

    
