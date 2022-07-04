{% autostrip %}

{{ x +}}
{{ y +}}
{{ l@_z +}}

{% set x="duh", y="duh" %}
{{ x +}}
{{ y +}}

{% set _d1 = _px ; else _d1 = "nothing" %}
{% set _d2 = p@py ; else _d2 = "nothing2" %}
{{ _d1 +}}
{{ _d2 +}}

{% set _global_ = 27 %} 
