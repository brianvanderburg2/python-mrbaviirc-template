{% autostrip %}
{% import lib="mrbaviirc.template" %}

{{ x +}}
{{ y +}}
{{ l@_z +}}

{% set x="duh", y="duh" %}
{{ x +}}
{{ y +}}

{{ lib.default(_px, "nothing") +}}
{{ lib.default(p@py, "nothing2") +}}

{% set _global_ = 27 %} 
