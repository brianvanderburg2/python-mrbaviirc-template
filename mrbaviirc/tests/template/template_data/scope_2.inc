{% set v1="Value 11", v3="Value 33" -%}
{{ v1 }}
{{ v2 }}
{{ v3 }}
{{ v4 }}
{{ v5 }}
{% global v2="Value 22" -%}
{% template v4 = "Value 300" -%}
