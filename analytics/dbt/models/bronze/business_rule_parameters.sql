-- Bronze model exposing the latest YAML business rules as generic key-value parameters.
select *
from {{ ref('business_rule_parameters_history') }}
where is_latest
