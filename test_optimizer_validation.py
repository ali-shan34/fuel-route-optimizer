
def brute_force_minimum_cost(
    route_distance,
    stations,
    starting_fuel=50,
    mpg=10,
):
    max_range = 500
    initial_range = int(starting_fuel * mpg)

    dp = {initial_range: 0.0}
    previous_position = 0

    ordered = sorted(
        stations,
        key=lambda station: station["distance_along_route"]
    )

    for station in ordered:
        position = int(station["distance_along_route"])
        travel = position - previous_position

        arrivals = {}

        for departure, cost in dp.items():
            arrival = departure - travel

            if arrival >= 0:
                if arrival not in arrivals or cost < arrivals[arrival]:
                    arrivals[arrival] = cost

        next_dp = {}

        for arrival, cost in arrivals.items():
            for departure in range(arrival, max_range + 1):
                purchase_cost = (
                    (departure - arrival) / mpg
                    * station["retail_price"]
                )

                total_cost = cost + purchase_cost

                if departure not in next_dp or total_cost < next_dp[departure]:
                    next_dp[departure] = total_cost

        dp = next_dp
        previous_position = position

    final_distance = int(route_distance - previous_position)

    possible_costs = [
        cost
        for fuel, cost in dp.items()
        if fuel >= final_distance
    ]

    if not possible_costs:
        raise ValueError("No feasible fuel plan.")

    return min(possible_costs)


stations = [
    {"station_id": 101, "retail_price": 3.00, "distance_along_route": 200},
    {"station_id": 102, "retail_price": 4.00, "distance_along_route": 400},
    {"station_id": 103, "retail_price": 3.50, "distance_along_route": 600},
]

reference_cost = brute_force_minimum_cost(
    route_distance=900,
    stations=stations,
)

print("Independent reference cost:", reference_cost)
print("Expected cost: 130.00")


print("\n--- EDGE CASE TESTS ---")

# Test 1: 500-mile route should need no fuel stop.
cost = brute_force_minimum_cost(
    route_distance=500,
    stations=[],
)

if cost == 0:
    print("PASS: 500-mile route needs no stop.")
else:
    print("FAIL: Unexpected fuel cost:", cost)


# Test 2: 501-mile route without stations is impossible.
try:
    brute_force_minimum_cost(
        route_distance=501,
        stations=[],
    )
    print("FAIL: Infeasible route was accepted.")
except ValueError:
    print("PASS: Route over 500 miles without stations rejected.")


# Test 3: Stations are too far apart.
far_apart_stations = [
    {
        "station_id": 201,
        "retail_price": 3.00,
        "distance_along_route": 200,
    },
    {
        "station_id": 202,
        "retail_price": 3.50,
        "distance_along_route": 800,
    },
]

try:
    brute_force_minimum_cost(
        route_distance=900,
        stations=far_apart_stations,
    )
    print("FAIL: Impossible station gap was accepted.")
except ValueError:
    print("PASS: Unreachable station gap rejected.")


import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from fuel.services.fuel_optimizer import optimize_fuel_stops

print("\n--- ACTUAL OPTIMIZER COMPARISON ---")

optimizer_stations = [
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

actual_result = optimize_fuel_stops(
    route_distance_miles=900,
    stations=optimizer_stations,
    starting_fuel=50,
)

print("Reference cost:", reference_cost)
print("Actual optimizer cost:", actual_result["total_fuel_cost"])
print("Actual optimizer stops:")

for stop in actual_result["stops"]:
    print(
        stop["name"],
        "Purchase:", stop["fuel_to_purchase_gallons"],
        "Cost:", stop["fuel_cost"],
    )

if abs(actual_result["total_fuel_cost"] - reference_cost) < 0.01:
    print("PASS: Both optimizers agree.")
else:
    print("FAIL: Optimizers produced different costs.")


print("\n--- ADDITIONAL PRICE TESTS ---")


test_cases = [
    {
        "name": "Cheap station later",
        "route": 900,
        "stations": [
            {
                "station_id": 201,
                "name": "Expensive Station",
                "city": "City A",
                "state": "TX",
                "retail_price": 5.00,
                "distance_along_route": 400,
            },
            {
                "station_id": 202,
                "name": "Cheap Station",
                "city": "City B",
                "state": "TX",
                "retail_price": 2.00,
                "distance_along_route": 600,
            },
        ],
    },
    {
        "name": "Three different fuel prices",
        "route": 1000,
        "stations": [
            {
                "station_id": 301,
                "name": "Station A",
                "city": "City A",
                "state": "TX",
                "retail_price": 4.00,
                "distance_along_route": 200,
            },
            {
                "station_id": 302,
                "name": "Station B",
                "city": "City B",
                "state": "TX",
                "retail_price": 2.00,
                "distance_along_route": 400,
            },
            {
                "station_id": 303,
                "name": "Station C",
                "city": "City C",
                "state": "TX",
                "retail_price": 3.00,
                "distance_along_route": 700,
            },
        ],
    },
]


for case in test_cases:
    reference = brute_force_minimum_cost(
        route_distance=case["route"],
        stations=case["stations"],
    )

    actual = optimize_fuel_stops(
        route_distance_miles=case["route"],
        stations=case["stations"],
        starting_fuel=50,
    )

    actual_cost = actual["total_fuel_cost"]

    print("\nTest:", case["name"])
    print("Reference cost:", round(reference, 2))
    print("Actual cost:", round(actual_cost, 2))

    if abs(reference - actual_cost) < 0.01:
        print("PASS: Costs match.")
    else:
        print("FAIL: Costs do not match.")


print("\n--- PARTIAL STARTING FUEL TEST ---")

partial_fuel_stations = [
    {
        "station_id": 401,
        "name": "Station A",
        "city": "City A",
        "state": "TX",
        "retail_price": 3.00,
        "distance_along_route": 200,
    },
    {
        "station_id": 402,
        "name": "Station B",
        "city": "City B",
        "state": "TX",
        "retail_price": 2.00,
        "distance_along_route": 400,
    },
]

reference = brute_force_minimum_cost(
    route_distance=700,
    stations=partial_fuel_stations,
    starting_fuel=30,
)

actual = optimize_fuel_stops(
    route_distance_miles=700,
    stations=partial_fuel_stations,
    starting_fuel=30,
)

print("Reference cost:", reference)
print("Actual cost:", actual["total_fuel_cost"])

if abs(reference - actual["total_fuel_cost"]) < 0.01:
    print("PASS: Partial starting fuel test.")
else:
    print("FAIL: Costs do not match.")


print("\n--- ACTUAL OPTIMIZER EDGE CASES ---")

# Test 1: 500 miles with full tank.
result = optimize_fuel_stops(
    route_distance_miles=500,
    stations=[],
    starting_fuel=50,
)

if result["stops"] == [] and result["total_fuel_cost"] == 0:
    print("PASS: Actual optimizer handles 500-mile route.")
else:
    print("FAIL: Unexpected result for 500-mile route.")


# Test 2: 501 miles without fuel stations.
try:
    optimize_fuel_stops(
        route_distance_miles=501,
        stations=[],
        starting_fuel=50,
    )
    print("FAIL: Actual optimizer accepted an impossible route.")

except ValueError:
    print("PASS: Actual optimizer rejects impossible route.")
