import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from fuel.services.fuel_optimizer import calculate_fuel_needed
from fuel.services.fuel_optimizer import find_reachable_stations

print("300 miles:", calculate_fuel_needed(300))
print("500 miles:", calculate_fuel_needed(500))
print("879.32 miles:", calculate_fuel_needed(879.32))

from fuel.services.fuel_optimizer import calculate_remaining_fuel

print("Remaining after 300 miles:",
      calculate_remaining_fuel(50, 300))

print("Remaining after 200 miles:",
      calculate_remaining_fuel(50, 200))

print("Remaining after 500 miles:",
      calculate_remaining_fuel(50, 500))

test_stations = [
    {"name": "Station A", "distance_along_route": 100},
    {"name": "Station B", "distance_along_route": 180},
    {"name": "Station C", "distance_along_route": 250},
    {"name": "Station D", "distance_along_route": 400},
]

reachable = find_reachable_stations(
    current_position=0,
    current_fuel=20,
    stations=test_stations,
)

print("Reachable stations:", reachable)