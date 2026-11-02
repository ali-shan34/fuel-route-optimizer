import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from fuel.models import FuelStation


class Command(BaseCommand):
    help = "Import fuel stations from the supplied CSV file."

    def handle(self, *args, **options):

        # 1. CSV file ka path
        csv_path = (
            Path(settings.BASE_DIR)
            / "data"
            / "fuel-prices-for-be-assessment.csv"
        )

        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        # 2. Required CSV columns
        required_columns = {
            "OPIS Truckstop ID",
            "Truckstop Name",
            "Address",
            "City",
            "State",
            "Rack ID",
            "Retail Price",
        }

        imported = 0
        duplicates = 0
        invalid = 0

        # 3. Existing database records ki identity load karo
        existing_records = set(
            FuelStation.objects.values_list(
                "station_id",
                "name",
                "address",
                "city",
                "state",
                "rack_id",
                "retail_price",
            )
        )

        seen_records = set(existing_records)
        stations_to_create = []

        # 4. CSV file read karo
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:

            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise CommandError("CSV file has no header row.")

            missing_columns = required_columns - set(reader.fieldnames)

            if missing_columns:
                raise CommandError(
                    f"Missing CSV columns: {', '.join(sorted(missing_columns))}"
                )

            for row in reader:

                try:
                    station_id = int(row["OPIS Truckstop ID"].strip())
                    name = row["Truckstop Name"].strip()
                    address = row["Address"].strip()
                    city = row["City"].strip()
                    state = row["State"].strip()
                    rack_id = int(row["Rack ID"].strip())
                    retail_price = Decimal(row["Retail Price"].strip())

                    # 5. Data validation
                    if (
                        not name
                        or not address
                        or not city
                        or not state
                        or len(state) > 10
                        or retail_price <= 0
                    ):
                        invalid += 1
                        continue

                    # 6. Duplicate detection
                    record_key = (
                        station_id,
                        name,
                        address,
                        city,
                        state,
                        rack_id,
                        retail_price,
                    )

                    if record_key in seen_records:
                        duplicates += 1
                        continue

                    seen_records.add(record_key)

                    # 7. Django model object create karo
                    station = FuelStation(
                        station_id=station_id,
                        name=name,
                        address=address,
                        city=city,
                        state=state,
                        rack_id=rack_id,
                        retail_price=retail_price,
                    )

                    stations_to_create.append(station)

                except (ValueError, TypeError, InvalidOperation):
                    invalid += 1
                    continue

        # 8. Database mein records insert karo
        with transaction.atomic():

            FuelStation.objects.bulk_create(
                stations_to_create,
                batch_size=500,
            )

        imported = len(stations_to_create)

        # 9. Final report
        self.stdout.write(self.style.SUCCESS("CSV import completed!"))

        self.stdout.write(f"Imported records: {imported}")
        self.stdout.write(f"Duplicate records skipped: {duplicates}")
        self.stdout.write(f"Invalid records skipped: {invalid}")
        self.stdout.write(
            f"Total CSV records processed: {imported + duplicates + invalid}"
        )