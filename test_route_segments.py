import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from fuel.services.geocoding import geocode_us_location
from fuel.services.routing import calculate_driving_route
from fuel.services.fuel_optimizer import (
    build_route_segments,
    find_stations_near_route,
    prepare_stations_for_optimization,
)

# Step 1: Get locations
start = geocode_us_location("New York, NY")
finish = geocode_us_location("Atlanta, GA")

# Step 2: Get driving route
route = calculate_driving_route(
    start_latitude=start["latitude"],
    start_longitude=start["longitude"],
    finish_latitude=finish["latitude"],
    finish_longitude=finish["longitude"],
)

# Step 3: Extract GeoJSON coordinates
coordinates = route["geometry"]["coordinates"]

# Step 4: Build route segments
segments = build_route_segments(
    coordinates,
    route_distance_miles=route["distance_miles"]
)

# Step 5: Display results
print("Total route segments:", len(segments))
print("First segment:", segments[0])
print("Last segment:", segments[-1])
print("Total segment distance:", round(segments[-1]["end_distance"], 2), "miles")
print("OSRM driving distance:", route["distance_miles"], "miles")



segments = build_route_segments(
    route["geometry"]["coordinates"],
    route_distance_miles=route["distance_miles"]
)

nearby_stations = find_stations_near_route(
    segments,
    corridor_miles=10,
)


print("Nearby stations found:", len(nearby_stations))
print("First 5 stations:", nearby_stations[:5])


prepared_stations = prepare_stations_for_optimization(
    nearby_stations
)

print("Original stations:", len(nearby_stations))
print("Prepared stations:", len(prepared_stations))
print("First 5 prepared stations:", prepared_stations[:5])

from fuel.services.fuel_optimizer import find_reachable_stations

reachable_stations = find_reachable_stations(
    current_position=0,
    current_fuel=50,
    stations=prepared_stations,
)

print("Total reachable stations:", len(reachable_stations))

print("First 10 reachable stations:")

for station in reachable_stations[:10]:
    print(
        station["name"],
        station["city"],
        station["state"],
        station["retail_price"],
        round(station["distance_along_route"], 2),
    )