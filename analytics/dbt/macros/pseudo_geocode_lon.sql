-- Derive deterministic pseudo-longitude coordinates from a postal address.
{% macro pseudo_geocode_lon(address_col) -%}
round(
    (
        3.70
        + (
            (
                (
                    coalesce(
                        cast(nullif(substring({{ address_col }} from '([0-9]{5})'), '') as numeric),
                        34970
                    )::integer / 10
                ) % 300
            ) / 1000.0
        )
        + ((('x' || substr(md5(coalesce({{ address_col }}, '')), 9, 8))::bit(32)::bigint % 1000) / 10000.0)
    )::numeric,
    6
)
{%- endmacro %}
