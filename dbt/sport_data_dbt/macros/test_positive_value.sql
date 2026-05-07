-- Generic dbt test ensuring a numeric field is strictly positive.
{% test positive_value(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} <= 0
{% endtest %}
