
from rest_framework import serializers

from fuel.models import FuelStation


class FuelStationSerializer(serializers.ModelSerializer):

    class Meta:
        model = FuelStation

        fields = [
            "id",
            "station_id",
            "name",
            "address",
            "city",
            "state",
            "rack_id",
            "retail_price",
            "latitude",
            "longitude",
            "coordinates_are_approximate",
        ]


class RouteRequestSerializer(serializers.Serializer):

    start = serializers.CharField(
        required=True,
        max_length=200,
        trim_whitespace=True
    )

    finish = serializers.CharField(
        required=True,
        max_length=200,
        trim_whitespace=True
    )

    def validate(self, data):

        if data["start"].lower() == data["finish"].lower():
            raise serializers.ValidationError(
                "Starting location and destination cannot be the same."
            )

        return data
