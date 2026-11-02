
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class RouteNotFoundError(Exception):
    pass


class RoutingServiceError(Exception):
    pass


def calculate_driving_route(
    start_latitude,
    start_longitude,
    finish_latitude,
    finish_longitude,
):
    """
    Calculate a driving route between two coordinates using OSRM.
    Returns distance, duration, and GeoJSON route geometry.
    """

    try:
        start_latitude = float(start_latitude)
        start_longitude = float(start_longitude)
        finish_latitude = float(finish_latitude)
        finish_longitude = float(finish_longitude)

    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid route coordinates.") from exc

    if not (
        -90 <= start_latitude <= 90
        and -90 <= finish_latitude <= 90
        and -180 <= start_longitude <= 180
        and -180 <= finish_longitude <= 180
    ):
        raise ValueError("Coordinates are outside valid ranges.")

    # OSRM expects longitude first, then latitude.
    coordinates = (
        f"{start_longitude},{start_latitude};"
        f"{finish_longitude},{finish_latitude}"
    )

    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{coordinates}"
        "?overview=full&geometries=geojson&steps=false"
    )

    request = Request(
        url,
        headers={"User-Agent": "fuel-route-optimizer/1.0"},
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RoutingServiceError(
            "Routing service is temporarily unavailable."
        ) from exc

    if data.get("code") == "NoRoute":
        raise RouteNotFoundError(
            "No driving route could be found between these locations."
        )

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingServiceError(
            "Routing service returned an invalid response."
        )

    route = data["routes"][0]

    distance_meters = route["distance"]
    duration_seconds = route["duration"]

    return {
        "distance_meters": distance_meters,
        "distance_miles": round(distance_meters / 1609.344, 2),
        "duration_seconds": duration_seconds,
        "duration_minutes": round(duration_seconds / 60, 2),
        "geometry": route["geometry"],
    }
