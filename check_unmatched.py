
import csv
import re
from collections import defaultdict
from django.db.models import Count

from fuel.models import FuelStation


canadian_states = [
    "ON", "AB", "BC", "MB", "SK",
    "YT", "QC", "NS", "NB"
]


def normalize_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


# Load Gazetteer places.
gazetteer = defaultdict(list)

with open(
    "data/2026_Gaz_place_national.txt",
    encoding="utf-8-sig",
    newline=""
) as file:

    reader = csv.DictReader(file, delimiter="|")

    for row in reader:
        state = row["USPS"].strip().upper()
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

        key = (normalize_name(city), state)

        gazetteer[key].append({
            "name": row["NAME"],
            "latitude": row["INTPTLAT"],
            "longitude": row["INTPTLONG"],
        })


# Find unmatched US cities.
unmatched = (
    FuelStation.objects
    .exclude(state__in=canadian_states)
    .filter(latitude__isnull=True)
    .values("city", "state")
    .annotate(station_count=Count("id"))
    .order_by("state", "city")
)

format_matches = []
no_matches = []
ambiguous_matches = []

for item in unmatched:

    city = item["city"].strip().lower()
    state = item["state"].strip().upper()

    key = (normalize_name(city), state)
    candidates = gazetteer.get(key, [])

    if len(candidates) == 1:
        format_matches.append((item, candidates[0]))

    elif len(candidates) > 1:
        ambiguous_matches.append((item, candidates))

    else:
        no_matches.append(item)


print("Formatting matches:", len(format_matches))
print("Ambiguous matches:", len(ambiguous_matches))
print("No Gazetteer matches:", len(no_matches))

print("\n--- POSSIBLE MATCHES ---")

for item, candidate in format_matches:
    print(
        item["city"],
        item["state"],
        "Stations:", item["station_count"],
        "Gazetteer:", candidate["name"]
    )

print("\n--- AMBIGUOUS MATCHES ---")

for item, candidates in ambiguous_matches:
    print(item["city"], item["state"], candidates)
