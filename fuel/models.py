from django.db import models

# Create your models here.

class FuelStation(models.Model):

    station_id = models.IntegerField()

    name = models.CharField(max_length=255)

    address = models.CharField(max_length=255)

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=10)

    rack_id = models.IntegerField()

    retail_price = models.DecimalField(
    max_digits=10,
    decimal_places=8
)

    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True
    )

    coordinates_are_approximate = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.name} - {self.city}"