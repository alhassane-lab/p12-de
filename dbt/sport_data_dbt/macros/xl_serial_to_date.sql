-- Convert an Excel date serial or timestamp-like string into a SQL date.
{% macro xl_serial_to_date(column_name) -%}
    case
        when nullif({{ column_name }}, '') is null then null
        when trim(cast({{ column_name }} as text)) ~ '^[0-9]+(\.[0-9]+)?$'
            then date '1899-12-30' + cast(cast({{ column_name }} as numeric) as integer)
        else cast(cast({{ column_name }} as timestamp) as date)
    end
{%- endmacro %}
