"""Deterministic distance and pseudo-geocoding helpers for the POC."""

import hashlib
import math
import re


OFFICE_COORDS = (43.5652, 3.9029)


def normalize_transport_mode(value: str | None) -> str:
    """Normalize raw transport labels so business rules can be applied safely."""
    if not value:
        return "inconnu"
    lowered = value.strip().lower()
    replacements = {
        "vélo": "velo",
        "vehicule thermique/electrique": "vehicule",
        "véhicule thermique/électrique": "vehicule",
    }
    return replacements.get(lowered, lowered)


def pseudo_geocode_address(address: str | None) -> tuple[float, float]:
    """Convert an address into deterministic pseudo-coordinates for offline demos."""
    if not address:
        return OFFICE_COORDS

    postal_match = re.search(r"\b(\d{5})\b", address)
    postal_code = int(postal_match.group(1)) if postal_match else 34970
    digest = hashlib.sha256(address.encode("utf-8")).hexdigest()
    lat_jitter = (int(digest[:8], 16) % 1000) / 10000
    lon_jitter = (int(digest[8:16], 16) % 1000) / 10000

    lat = 43.40 + ((postal_code % 300) / 1000) + lat_jitter
    lon = 3.70 + (((postal_code // 10) % 300) / 1000) + lon_jitter
    return round(lat, 6), round(lon, 6)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great-circle distance between two points in kilometers."""
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return round(2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)
