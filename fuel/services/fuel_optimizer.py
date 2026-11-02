
import math
from fuel.models import FuelStation
MAX_RANGE_MILES = 500
FUEL_ECONOMY_MPG = 10

TANK_CAPACITY_GALLONS = (
    MAX_RANGE_MILES / FUEL_ECONOMY_MPG
)

def calculate_fuel_needed(distance_miles, mpg=FUEL_ECONOMY_MPG):
    """
    Calculate fuel required for a given distance.
    """

    if distance_miles < 0:
        raise ValueError("Distance cannot be negative.")

    if mpg <= 0:
        raise ValueError("MPG must be greater than zero.")

    return distance_miles / mpg


def calculate_remaining_fuel(
    current_fuel,
    distance_miles,
    mpg=FUEL_ECONOMY_MPG,
):
    """
    Calculate remaining fuel after driving a distance.
    """

    if current_fuel < 0:
        raise ValueError("Current fuel cannot be negative.")

    if current_fuel > TANK_CAPACITY_GALLONS:
        raise ValueError("Fuel cannot exceed tank capacity.")

    fuel_used = calculate_fuel_needed(distance_miles, mpg)

    if fuel_used > current_fuel:
        raise ValueError("Not enough fuel to complete this distance.")

    return current_fuel - fuel_used


def find_reachable_stations(
    current_position,
    current_fuel,
    stations,
    mpg=FUEL_ECONOMY_MPG,
):
    """
    Find fuel stations reachable with the current fuel.
    """

    available_range = current_fuel * mpg

    reachable_stations = []

    for station in stations:

        distance = (
            station["distance_along_route"] - current_position
        )

        if 0 < distance <= available_range:
            reachable_stations.append(station)

    return reachable_stations



def calculate_distance_miles(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates in miles.
    """

    earth_radius_miles = 3958.8

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    latitude_difference = lat2 - lat1
    longitude_difference = lon2 - lon1

    a = (
        math.sin(latitude_difference / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(longitude_difference / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius_miles * c


def build_route_segments(route_coordinates, route_distance_miles=None):
    """
    Convert GeoJSON route coordinates into segments
    with cumulative distance from the route start.

    If OSRM route distance is provided, scale the
    Haversine segment distances to match it.
    """

    segments = []
    cumulative_distance = 0.0

    for index in range(len(route_coordinates) - 1):

        lon1, lat1 = route_coordinates[index]
        lon2, lat2 = route_coordinates[index + 1]

        segment_distance = calculate_distance_miles(
            lat1, lon1, lat2, lon2
        )

        segment = {
            "start": (lon1, lat1),
            "end": (lon2, lat2),
            "start_distance": cumulative_distance,
            "end_distance": cumulative_distance + segment_distance,
            "length": segment_distance,
        }

        segments.append(segment)
        cumulative_distance += segment_distance

    # Scale segment distances to match OSRM distance.
    if route_distance_miles is not None:

        if cumulative_distance <= 0:
            raise ValueError("Invalid route geometry.")

        scale_factor = route_distance_miles / cumulative_distance

        cumulative_distance = 0.0

        for segment in segments:
            segment["length"] *= scale_factor
            segment["start_distance"] = cumulative_distance

            cumulative_distance += segment["length"]

            segment["end_distance"] = cumulative_distance

    return segments

def project_station_onto_segment(
    station_lat,
    station_lon,
    segment,
):
    """
    Project a station onto a route segment.
    Returns its distance from the segment start
    and its distance from the route.
    """

    start_lon, start_lat = segment["start"]
    end_lon, end_lat = segment["end"]

    reference_lat = math.radians(
        (start_lat + end_lat + station_lat) / 3
    )

    miles_per_degree_lat = 69.0
    miles_per_degree_lon = (
        69.172 * math.cos(reference_lat)
    )

    dx = (end_lon - start_lon) * miles_per_degree_lon
    dy = (end_lat - start_lat) * miles_per_degree_lat

    station_x = (
        (station_lon - start_lon) * miles_per_degree_lon
    )
    station_y = (
        (station_lat - start_lat) * miles_per_degree_lat
    )

    segment_length_squared = dx * dx + dy * dy

    if segment_length_squared == 0:
        projection_ratio = 0.0
    else:
        projection_ratio = (
            station_x * dx + station_y * dy
        ) / segment_length_squared

    projection_ratio = max(0.0, min(1.0, projection_ratio))

    projected_x = projection_ratio * dx
    projected_y = projection_ratio * dy

    distance_from_route = math.sqrt(
        (station_x - projected_x) ** 2
        + (station_y - projected_y) ** 2
    )

    distance_along_segment = (
        projection_ratio * segment["length"]
    )

    return {
        "distance_from_route": distance_from_route,
        "distance_along_segment": distance_along_segment,
        "projection_ratio": projection_ratio,
    }
def locate_station_on_route(
    station_lat,
    station_lon,
    route_segments,
):
    """
    Find the closest point on the route to a fuel station.
    """

    best_match = None

    for segment in route_segments:

        projection = project_station_onto_segment(
            station_lat,
            station_lon,
            segment,
        )

        if (
            best_match is None
            or projection["distance_from_route"]
            < best_match["distance_from_route"]
        ):

            best_match = {
                "distance_from_route": projection[
                    "distance_from_route"
                ],
                "distance_along_route": (
                    segment["start_distance"]
                    + projection["distance_along_segment"]
                ),
            }

    return best_match

def find_stations_near_route(route_segments, corridor_miles=10):
    """
    Find fuel stations within a specified distance of the route.
    """

    stations = FuelStation.objects.exclude(
        latitude__isnull=True
    ).exclude(
        longitude__isnull=True
    )

    nearby_stations = []

    for station in stations:

        location = locate_station_on_route(
            station.latitude,
            station.longitude,
            route_segments,
        )

        if location is None:
            continue

        if location["distance_from_route"] <= corridor_miles:

            nearby_stations.append({
                "station_id": station.station_id,
                "name": station.name,
                "city": station.city,
                "state": station.state,
                "retail_price": float(station.retail_price),
                "latitude": station.latitude,
                "longitude": station.longitude,
                "distance_from_route": location["distance_from_route"],
                "distance_along_route": location["distance_along_route"],
                "coordinates_are_approximate": (
                    station.coordinates_are_approximate
                ),
            })

    return nearby_stations


def find_stations_near_route_fast(
    route_segments,
    corridor_miles=10,
):
    """
    Use a geographic grid to shortlist route segments
    before calculating exact station-to-route distances.
    """

    cell_size = 0.1
    segment_grid = {}

    # Step 1: Build a grid index for route segments.
    for index, segment in enumerate(route_segments):

        start_lon, start_lat = segment["start"]
        end_lon, end_lat = segment["end"]

        min_lat = math.floor(
            min(start_lat, end_lat) / cell_size
        )
        max_lat = math.floor(
            max(start_lat, end_lat) / cell_size
        )

        min_lon = math.floor(
            min(start_lon, end_lon) / cell_size
        )
        max_lon = math.floor(
            max(start_lon, end_lon) / cell_size
        )

        for lat_cell in range(min_lat, max_lat + 1):
            for lon_cell in range(min_lon, max_lon + 1):

                key = (lat_cell, lon_cell)

                segment_grid.setdefault(key, []).append(index)

    # Step 2: Load stations with coordinates.
    stations = FuelStation.objects.exclude(
        latitude__isnull=True
    ).exclude(
        longitude__isnull=True
    )

    nearby_stations = []

    # Step 3: Check only nearby grid cells.
    for station in stations:

        lat_cell = math.floor(
            station.latitude / cell_size
        )
        lon_cell = math.floor(
            station.longitude / cell_size
        )

        lat_radius = (
            math.ceil(
                corridor_miles / 69.0 / cell_size
            ) + 1
        )

        longitude_scale = (
            69.172
            * max(
                abs(math.cos(math.radians(station.latitude))),
                0.05,
            )
        )

        lon_radius = (
            math.ceil(
                corridor_miles / longitude_scale / cell_size
            ) + 1
        )

        candidate_indices = set()

        for lat_offset in range(-lat_radius, lat_radius + 1):
            for lon_offset in range(-lon_radius, lon_radius + 1):

                key = (
                    lat_cell + lat_offset,
                    lon_cell + lon_offset,
                )

                candidate_indices.update(
                    segment_grid.get(key, [])
                )

        best_match = None

        # Step 4: Calculate exact distances for candidates.
        for index in candidate_indices:

            segment = route_segments[index]

            projection = project_station_onto_segment(
                station.latitude,
                station.longitude,
                segment,
            )

            if (
                best_match is None
                or projection["distance_from_route"]
                < best_match["distance_from_route"]
            ):

                best_match = {
                    "distance_from_route": projection[
                        "distance_from_route"
                    ],
                    "distance_along_route": (
                        segment["start_distance"]
                        + projection["distance_along_segment"]
                    ),
                }

        if best_match is None:
            continue

        if best_match["distance_from_route"] <= corridor_miles:

            nearby_stations.append({
                "station_id": station.station_id,
                "name": station.name,
                "city": station.city,
                "state": station.state,
                "retail_price": float(station.retail_price),
                "latitude": station.latitude,
                "longitude": station.longitude,
                "distance_from_route": (
                    best_match["distance_from_route"]
                ),
                "distance_along_route": (
                    best_match["distance_along_route"]
                ),
                "coordinates_are_approximate": (
                    station.coordinates_are_approximate
                ),
            })

    return nearby_stations



def prepare_stations_for_optimization(stations):
    """
    Remove duplicate station records and sort stations
    by their position along the route.
    """

    unique_stations = {}

    for station in stations:
        station_key = (
            station["station_id"],
            station["city"],
            station["state"],
        )

        existing = unique_stations.get(station_key)

        if (
            existing is None
            or station["retail_price"] < existing["retail_price"]
        ):
            unique_stations[station_key] = station

    prepared_stations = list(unique_stations.values())

    prepared_stations.sort(
        key=lambda station: station["distance_along_route"]
    )

    return prepared_stations


def optimize_fuel_stops(
    route_distance_miles,
    stations,
    starting_fuel=TANK_CAPACITY_GALLONS,
    mpg=FUEL_ECONOMY_MPG,
):
    """
    Find a minimum-cost feasible fuel plan using
    dynamic programming with 0.1-mile fuel increments.

    Fuel purchases happen at stations.
    Starting fuel is already available in the vehicle.
    """

    if route_distance_miles <= 0:
        raise ValueError("Route distance must be positive.")

    if mpg <= 0:
        raise ValueError("MPG must be greater than zero.")

    if not 0 <= starting_fuel <= TANK_CAPACITY_GALLONS:
        raise ValueError("Invalid starting fuel amount.")

    unit_miles = 0.1
    max_range_units = math.floor(
        MAX_RANGE_MILES / unit_miles + 1e-9
    )

    initial_range = min(
        max_range_units,
        math.floor(starting_fuel * mpg / unit_miles + 1e-9),
    )

    # Common response structure for every successful route.
    if route_distance_miles <= initial_range * unit_miles:
        return {
            "stops": [],
            "total_fuel_cost": 0.0,
            "total_fuel_purchased_gallons": 0.0,
            "route_distance_miles": route_distance_miles,
            "starting_fuel_gallons": starting_fuel,
            "fuel_consumed_gallons": round(
                route_distance_miles / mpg, 3
            ),
            "estimated_fuel_remaining_gallons": round(
                starting_fuel - route_distance_miles / mpg, 3
            ),
            "optimization_resolution_miles": unit_miles,
        }

    # Keep valid stations located between origin and destination.
    ordered_stations = []

    for station in stations:

        position = float(station["distance_along_route"])
        price = float(station["retail_price"])

        if (
            0 < position < route_distance_miles
            and price > 0
        ):
            ordered_stations.append(station)

    ordered_stations.sort(
        key=lambda station: station["distance_along_route"]
    )

    if not ordered_stations:
        raise ValueError("No feasible fuel stations found.")

    infinity = float("inf")

    # Calculate fuel required to reach the first station.
    first_station_position = float(
        ordered_stations[0]["distance_along_route"]
    )

    first_travel_units = math.ceil(
        first_station_position / unit_miles - 1e-9
    )

    if first_travel_units > initial_range:
        raise ValueError(
            "No feasible fuel plan can reach the first station."
        )

    # DP state: minimum cost for each possible arrival fuel range.
    dp = [infinity] * (max_range_units + 1)

    first_remaining = initial_range - first_travel_units
    dp[first_remaining] = 0.0

    parent_history = []

    # Process each station and then the destination.
    for index, station in enumerate(ordered_stations):

        current_position = float(
            station["distance_along_route"]
        )

        if index + 1 < len(ordered_stations):
            next_position = float(
                ordered_stations[index + 1]["distance_along_route"]
            )
        else:
            next_position = route_distance_miles

        travel_units = math.ceil(
            (next_position - current_position) / unit_miles - 1e-9
        )

        unit_cost = (
            unit_miles / mpg
            * float(station["retail_price"])
        )

        next_dp = [infinity] * (max_range_units + 1)
        next_parent = [None] * (max_range_units + 1)

        best_adjusted_cost = infinity
        best_arrival_range = None

        # For each departure range, find the cheapest
        # possible arrival state at the current station.
        for departure_range in range(max_range_units + 1):

            arrival_cost = dp[departure_range]

            if arrival_cost != infinity:

                adjusted_cost = (
                    arrival_cost - departure_range * unit_cost
                )

                if adjusted_cost < best_adjusted_cost:
                    best_adjusted_cost = adjusted_cost
                    best_arrival_range = departure_range

            remaining_range = departure_range - travel_units

            if (
                remaining_range >= 0
                and best_arrival_range is not None
            ):
                next_dp[remaining_range] = (
                    best_adjusted_cost
                    + departure_range * unit_cost
                )

                next_parent[remaining_range] = (
                    best_arrival_range,
                    departure_range,
                )

        dp = next_dp
        parent_history.append(next_parent)

    # Find the cheapest feasible arrival at the destination.
    best_destination_range = None
    best_total_cost = infinity

    for remaining_range, cost in enumerate(dp):

        if cost < best_total_cost:
            best_total_cost = cost
            best_destination_range = remaining_range

    if best_destination_range is None:
        raise ValueError(
            "No feasible fuel plan can reach the destination."
        )

    # Reconstruct purchases at each station.
    stops = []
    current_remaining = best_destination_range

    for index in range(len(ordered_stations) - 1, -1, -1):

        parent = parent_history[index][current_remaining]

        if parent is None:
            raise ValueError(
                "Fuel plan reconstruction failed."
            )

        arrival_range, departure_range = parent

        purchased_units = departure_range - arrival_range

        if purchased_units > 0:

            station = ordered_stations[index]

            gallons = purchased_units * unit_miles / mpg
            price = float(station["retail_price"])

            stops.append({
                "station_id": station["station_id"],
                "name": station["name"],
                "city": station["city"],
                "state": station["state"],
                "retail_price": price,
                "distance_along_route": float(
                    station["distance_along_route"]
                ),
                "fuel_to_purchase_gallons": round(gallons, 3),
                "fuel_cost": round(gallons * price, 2),
                "coordinates_are_approximate": (
                    station.get("coordinates_are_approximate", True)
                ),
            })

        # Move backwards to the previous station's arrival state.
        current_remaining = arrival_range

    stops.reverse()

    # Use displayed stop costs for a consistent API total.
    total_fuel_cost = sum(
        stop["fuel_cost"] for stop in stops
    )

    total_purchased = sum(
        stop["fuel_to_purchase_gallons"] for stop in stops
    )

    fuel_consumed = route_distance_miles / mpg

    estimated_remaining = (
        starting_fuel
        + total_purchased
        - fuel_consumed
    )

    return {
        "stops": stops,
        "total_fuel_cost": round(total_fuel_cost, 2),
        "total_fuel_purchased_gallons": round(
            total_purchased, 3
        ),
        "route_distance_miles": round(
            route_distance_miles, 2
        ),
        "starting_fuel_gallons": starting_fuel,
        "fuel_consumed_gallons": round(fuel_consumed, 3),
        "estimated_fuel_remaining_gallons": round(
            estimated_remaining, 3
        ),
        "optimization_resolution_miles": unit_miles,
    }
