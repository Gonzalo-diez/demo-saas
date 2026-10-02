from h3 import (latlng_to_cell, grid_disk, average_hexagon_edge_length, is_valid_cell)
from math import ceil

H3_RESOLUTION = 9

def validate_coordinates(
    lat: float,
    lng: float,
) -> None:

    if not (-90 <= lat <= 90):
        raise ValueError("Latitud inválida")

    if not (-180 <= lng <= 180):
        raise ValueError("Longitud inválida")

def compute_h3(
    lat: float | None,
    lng: float | None,
) -> str | None:

    if (lat is None) != (lng is None):
        raise ValueError(
            "lat y lng deben venir juntos"
        )

    if lat is None and lng is None:
        return None

    lat = float(lat)
    lng = float(lng)

    validate_coordinates(lat, lng)

    h3_index = latlng_to_cell(
        lat,
        lng,
        H3_RESOLUTION,
    )

    return h3_index

def km_to_h3_k(radius_km: float) -> int:
    """
    Convierte kilómetros aproximados
    a cantidad de anillos H3.
    """
    
    if radius_km <= 0:
        raise ValueError(
            "radius_km debe ser mayor a 0"
        )

    edge_km = average_hexagon_edge_length(
        H3_RESOLUTION,
        unit="km",
    )

    return max(
        1,
        ceil(radius_km / edge_km),
    )

def compute_h3_coverage(
    lat: float,
    lng: float,
    radius_km: float,
) -> list[str]:

    center = compute_h3(
        lat,
        lng,
    )
    
    if center is None:
        return []

    radius_k = km_to_h3_k(
        radius_km,
    )

    return list(
        grid_disk(center, radius_k)
    )