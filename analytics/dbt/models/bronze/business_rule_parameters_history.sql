-- Bronze model exposing the full history of YAML business rules as key-value parameters.
with rule_history as (
    select
        rule_version,
        effective_from,
        effective_to_exclusive,
        loaded_at,
        is_current
    from {{ ref('business_rules_validity') }}
)
select
    p.rule_version,
    h.effective_from,
    h.effective_to_exclusive,
    p.rule_path,
    p.rule_value_json,
    p.value_type,
    p.loaded_at,
    h.is_current as is_latest
from {{ source('raw', 'business_rule_parameters_raw') }} p
inner join rule_history h
    on p.rule_version = h.rule_version
