
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from fuel.models import FuelStation
from fuel.serializers import (
    FuelStationSerializer,
    RouteRequestSerializer,
)

from fuel.services.geocoding import (
    geocode_us_location,
    LocationNotFoundError,
    GeocodingServiceError,
)

from fuel.services.routing import (
    calculate_driving_route,
    RouteNotFoundError,
    RoutingServiceError,
)

from fuel.services.fuel_optimizer import (
    build_route_segments,
    find_stations_near_route_fast,
    prepare_stations_for_optimization,
    optimize_fuel_stops,
)


class FuelStationListAPIView(generics.ListAPIView):
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer


class RouteAPIView(APIView):

    def post(self, request):

        # Step 1: Validate user input.
        serializer = RouteRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        start = serializer.validated_data["start"]
        finish = serializer.validated_data["finish"]

        try:
            # Step 2: Convert locations into coordinates.
            start_location = geocode_us_location(start)
            finish_location = geocode_us_location(finish)

            # Step 3: Calculate actual driving route using OSRM.
            route = calculate_driving_route(
                start_latitude=start_location["latitude"],
                start_longitude=start_location["longitude"],
                finish_latitude=finish_location["latitude"],
                finish_longitude=finish_location["longitude"],
            )

            # Step 4: Build route segments.
            segments = build_route_segments(
                route["geometry"]["coordinates"],
                route_distance_miles=route["distance_miles"],
            )

            # Step 5: Find fuel stations near the route.
            stations = FuelStation.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False,
            )

            nearby_stations = find_stations_near_route_fast(
                route_segments=segments,
                corridor_miles=10,
            )

            # Step 6: Remove duplicate station entries.
            prepared_stations = prepare_stations_for_optimization(
                nearby_stations
            )

            # Step 7: Calculate the fuel plan.
            fuel_plan = optimize_fuel_stops(
                route_distance_miles=route["distance_miles"],
                stations=prepared_stations,
                starting_fuel=50,
                mpg=10,
            )

        except LocationNotFoundError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except RouteNotFoundError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except GeocodingServiceError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except RoutingServiceError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 8: Return complete route and fuel plan.
        return Response(
            {
                "message": "Route calculated successfully.",
                "start": start_location,
                "finish": finish_location,
                "route": route,
                "route_segments_count": len(segments),
                "route_segments_total_miles": round(
                    segments[-1]["end_distance"], 2
                ) if segments else 0,
                "fuel_stations_found": len(nearby_stations),
                "fuel_stations_after_deduplication": len(prepared_stations),
                "fuel_plan": fuel_plan,
            },
            status=status.HTTP_200_OK
        )
