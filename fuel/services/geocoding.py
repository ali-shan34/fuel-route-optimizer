import hashlib

from django.core.cache import cache
from geopy.exc import GeocoderServiceError as GeopyServiceError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


class LocationNotFoundError(Exception):
    pass


class GeocodingServiceError(Exception):
    pass


# Connect to OpenStreetMap's Nominatim service.
geolocator = Nominatim(
    user_agent="fuel-route-optimizer-assessment/1.0",
    timeout=10,
)

# Keep at least 1.1 seconds between requests.
geocode_with_limit = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1.1,
    max_retries=1,
    error_wait_seconds=2,
    swallow_exceptions=False,
)


def geocode_us_location(query):
    """
    Convert a US location name into latitude and longitude.
    Cache successful results to avoid repeated API requests.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Location cannot be empty.")

    normalized_query = " ".join(query.strip().split())

    # Generate a unique cache key for this location.
    cache_key = "geocode_" + hashlib.sha256(
        normalized_query.lower().encode("utf-8")
    ).hexdigest()

    # Return cached result if available.
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        return cached_result

    try:
        location = geocode_with_limit(
            normalized_query,
            exactly_one=True,
            addressdetails=True,
            country_codes="us",
        )

    except GeopyServiceError as exc:
        raise GeocodingServiceError(
            "Geocoding service is temporarily unavailable."
        ) from exc

    if location is None:
        raise LocationNotFoundError(
            f"Could not find this US location: {normalized_query}"
        )

    # Verify the returned location is actually in the USA.
    address = location.raw.get("address", {})
    country_code = address.get("country_code", "").lower()

    if country_code != "us":
        raise LocationNotFoundError(
            "Start and finish locations must be inside the USA."
        )

    result = {
        "query": normalized_query,
        "display_name": location.address,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "country_code": country_code,
    }

    # Cache successful results for 30 days.
    cache.set(cache_key, result, timeout=60 * 60 * 24 * 30)

    return result