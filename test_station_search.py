
import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from fuel.services.geocoding import geocode_us_location
from fuel.services.routing import calculate_driving_route
from fuel.services.fuel_optimizer import (
    build_route_segments,
    find_stations_near_route_fast,
)
from fuel.services.fuel_optimizer import (
    build_route_segments,
    find_stations_near_route,
    find_stations_near_route_fast,
)

print("Geocoding locations...")

start = geocode_us_location("New York, NY")
finish = geocode_us_location("Atlanta, GA")

print("Calculating driving route...")

route = calculate_driving_route(
    start_latitude=start["latitude"],
    start_longitude=start["longitude"],
    finish_latitude=finish["latitude"],
    finish_longitude=finish["longitude"],
)

segments = build_route_segments(
    route["geometry"]["coordinates"]
)

print("Route segments:", len(segments))

print("Searching nearby fuel stations...")

start_time = time.perf_counter()

nearby = find_stations_near_route_fast(
    segments,
    corridor_miles=10,
)

elapsed = time.perf_counter() - start_time

print("Nearby stations:", len(nearby))
print("Search time:", round(elapsed, 2), "seconds")


print("\n--- ORIGINAL SEARCH ---")

start_time = time.perf_counter()

original_results = find_stations_near_route(
    segments,
    corridor_miles=10,
)

original_time = time.perf_counter() - start_time

print("Original stations:", len(original_results))
print("Original time:", round(original_time, 2), "seconds")


print("\n--- OPTIMIZED SEARCH ---")

start_time = time.perf_counter()

fast_results = find_stations_near_route_fast(
    segments,
    corridor_miles=10,
)

fast_time = time.perf_counter() - start_time

print("Fast stations:", len(fast_results))
print("Fast time:", round(fast_time, 2), "seconds")


# Compare station identity.
def station_key(station):
    return (
        station["station_id"],
        station["city"],
        station["state"],
    )


original_map = {
    station_key(station): station
    for station in original_results
}

fast_map = {
    station_key(station): station
    for station in fast_results
}

missing = set(original_map) - set(fast_map)
extra = set(fast_map) - set(original_map)

print("\n--- ACCURACY COMPARISON ---")
print("Missing stations:", len(missing))
print("Extra stations:", len(extra))

if not missing and not extra:
    print("PASS: Both searches found the same stations.")
else:
    print("FAIL: Search results differ.")


# Compare route positions and distances.
if not missing and not extra:
    max_position_difference = max(
        (
            abs(
                original_map[key]["distance_along_route"]
                - fast_map[key]["distance_along_route"]
            )
            for key in original_map
        ),
        default=0,
    )

    max_distance_difference = max(
        (
            abs(
                original_map[key]["distance_from_route"]
                - fast_map[key]["distance_from_route"]
            )
            for key in original_map
        ),
        default=0,
    )

    print(
        "Maximum route-position difference:",
        round(max_position_difference, 6),
        "miles",
    )

    print(
        "Maximum route-distance difference:",
        round(max_distance_difference, 6),
        "miles",
    )
