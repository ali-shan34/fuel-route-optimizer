
import csv
import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from fuel.models import FuelStation


US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE",
    "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS",
    "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
}


def normalize_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


class Command(BaseCommand):
    help = "Add approximate city coordinates to US fuel stations."

    def handle(self, *args, **options):

        gazetteer_file = (
            Path("data") / "2026_Gaz_place_national.txt"
        )

        if not gazetteer_file.exists():
            self.stdout.write(
                self.style.ERROR("Gazetteer file not found.")
            )
            return

        # Step 1: Load Gazetteer coordinates.
        city_coordinates = {}
        ambiguous_places = set()

        with open(
            gazetteer_file,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file, delimiter="|")

            for row in reader:

                state = row["USPS"].strip().upper()

                if state not in US_STATE_CODES:
                    continue

                city = row["NAME"].strip().lower()

                for suffix in (
                    " city",
                    " town",
                    " village",
                    " borough",
                    " cdp",
                ):
                    if city.endswith(suffix):
                        city = city[:-len(suffix)].strip()
                        break

                # Known Gazetteer naming difference.
                if state == "ID" and city == "boise city":
                    city = "boise"

                key = (normalize_name(city), state)

                coordinates = (
                    float(row["INTPTLAT"]),
                    float(row["INTPTLONG"]),
                )

                if key in ambiguous_places:
                    continue

                if key in city_coordinates:
                    if city_coordinates[key] != coordinates:
                        city_coordinates.pop(key)
                        ambiguous_places.add(key)
                else:
                    city_coordinates[key] = coordinates

        self.stdout.write(
            f"Loaded {len(city_coordinates)} unique US places."
        )

        # Step 2: Match stations.
        matched = 0
        unmatched = 0
        already_has_coordinates = 0
        ambiguous_count = 0
        non_us_skipped = 0

        with transaction.atomic():

            stations = FuelStation.objects.all()

            for station in stations:

                state = station.state.strip().upper()

                if state not in US_STATE_CODES:
                    non_us_skipped += 1
                    continue

                if (
                    station.latitude is not None
                    and station.longitude is not None
                ):
                    already_has_coordinates += 1
                    continue

                key = (
                    normalize_name(station.city.strip()),
                    state,
                )

                if key in ambiguous_places:
                    ambiguous_count += 1
                    unmatched += 1
                    continue

                coordinates = city_coordinates.get(key)

                if coordinates is None:
                    unmatched += 1
                    continue

                station.latitude = coordinates[0]
                station.longitude = coordinates[1]
                station.coordinates_are_approximate = True

                station.save(
                    update_fields=[
                        "latitude",
                        "longitude",
                        "coordinates_are_approximate",
                    ]
                )

                matched += 1

        # Step 3: Report results.
        self.stdout.write(
            self.style.SUCCESS(f"Newly matched: {matched}")
        )

        self.stdout.write(
            self.style.WARNING(f"Unmatched US stations: {unmatched}")
        )

        self.stdout.write(
            f"Already had coordinates: {already_has_coordinates}"
        )

        self.stdout.write(
            f"Ambiguous station matches: {ambiguous_count}"
        )

        self.stdout.write(
            f"Non-US stations skipped: {non_us_skipped}"
        )
