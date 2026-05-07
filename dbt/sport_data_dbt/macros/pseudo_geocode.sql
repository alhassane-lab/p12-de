-- Derive deterministic pseudo-latitude coordinates from a postal address.
{% macro pseudo_geocode_lat(address_col) -%}
round(
    (
        43.40
        + (
            (
                coalesce(
                    cast(nullif(substring({{ address_col }} from '([0-9]{5})'), '') as numeric),
                    34970
                )::integer % 300
            ) / 1000.0
        )
        + ((('x' || substr(md5(coalesce({{ address_col }}, '')), 1, 8))::bit(32)::bigint % 1000) / 10000.0)
    )::numeric,
    6
)
{%- endmacro %}
