"""Unit tests covering deterministic distance and transport normalization helpers."""

from pipeline.utils.distance import haversine_km, normalize_transport_mode, pseudo_geocode_address


def test_normalize_transport_mode():
    """Transport labels should be normalized to a small controlled vocabulary."""
    assert normalize_transport_mode("Vélo") == "velo"
    assert normalize_transport_mode("véhicule thermique/électrique") == "vehicule"


def test_pseudo_geocode_is_deterministic():
    """The same address must always produce the same pseudo-coordinates."""
    coords_a = pseudo_geocode_address("53 Av. de la Gare, 34970 Lattes")
    coords_b = pseudo_geocode_address("53 Av. de la Gare, 34970 Lattes")
    assert coords_a == coords_b


def test_haversine_non_negative():
    """Distance between identical points should be exactly zero."""
    assert haversine_km(43.5652, 3.9029, 43.5652, 3.9029) == 0
