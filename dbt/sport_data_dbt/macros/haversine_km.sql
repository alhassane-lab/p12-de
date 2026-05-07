-- Return the haversine distance in kilometers between two latitude/longitude pairs.
{% macro haversine_km(lat1, lon1, lat2, lon2) -%}
round(
    (
        6371 * 2 * asin(
            sqrt(
                power(sin(radians(({{ lat2 }}) - ({{ lat1 }})) / 2), 2)
                + cos(radians({{ lat1 }}))
                * cos(radians({{ lat2 }}))
                * power(sin(radians(({{ lon2 }}) - ({{ lon1 }})) / 2), 2)
            )
        )
    )::numeric,
    2
)
{%- endmacro %}
