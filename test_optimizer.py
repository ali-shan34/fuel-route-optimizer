import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from fuel.services.fuel_optimizer import optimize_fuel_stops

stations = [
    {
        "station_id": 101,
        "name": "Cheap Station",
        "city": "City A",
        "state": "TX",
        "retail_price": 3.00,
        "distance_along_route": 200,
    },
    {
        "station_id": 102,
        "name": "Expensive Station",
        "city": "City B",
        "state": "TX",
        "retail_price": 4.00,
        "distance_along_route": 400,
    },
    {
        "station_id": 103,
        "name": "Medium Station",
        "city": "City C",
        "state": "TX",
        "retail_price": 3.50,
        "distance_along_route": 600,
    },
]

result = optimize_fuel_stops(
    route_distance_miles=900,
    stations=stations,
    starting_fuel=50,
)

print("Optimization result:")
print(result)