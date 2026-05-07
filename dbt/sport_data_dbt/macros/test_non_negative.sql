-- Generic dbt test ensuring a numeric field never drops below zero.
{% test non_negative(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} < 0
{% endtest %}
