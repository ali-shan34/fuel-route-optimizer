# Fuel Route Optimizer API

A Django REST Framework API that calculates driving routes between US locations and recommends fuel stops based on fuel prices from the provided assessment dataset.

## Features

- Calculate driving routes between US locations.
- Retrieve route distance and estimated duration.
- Find fuel stations near the driving route.
- Recommend fuel stops based on fuel prices and vehicle range.
- List fuel stations through a paginated API.
- Validate route requests and handle invalid locations.

## Technology Stack

- Python
- Django
- Django REST Framework
- SQLite
- Nominatim for geocoding
- OSRM for driving routes
- Postman for API testing

## Vehicle Configuration

| Setting | Value |
|---|---:|
| Maximum driving range | 500 miles |
| Fuel efficiency | 10 MPG |
| Fuel tank capacity | 50 gallons |
| Optimization resolution | 0.1 miles |

## Project Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd fuel-route-optimizer
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Import fuel station data

Place the assessment CSV file in the `data` directory, then run:

```bash
python manage.py import_fuel_stations
```

### 6. Add approximate station coordinates

```bash
python manage.py add_station_coordinates
```

### 7. Start the development server

```bash
python manage.py runserver
```

## API Endpoints

### List Fuel Stations

**GET**

```text
http://127.0.0.1:8000/api/stations/
```

Returns a paginated list of fuel stations.

### Optimize Route

**POST**

```text
http://127.0.0.1:8000/api/route/
```

Example request body:

```json
{
  "start": "New York, NY",
  "finish": "Atlanta, GA"
}
```

## Route Optimization Workflow

1. Geocode the starting and destination locations.
2. Retrieve the driving route using OSRM.
3. Identify fuel stations near the route.
4. Prepare and deduplicate station data.
5. Calculate fuel requirements and recommend stops based on fuel prices and vehicle range.

## Running Tests

Run the project test scripts:

```bash
python test_fuel_calculation.py
python test_optimizer.py
python test_optimizer_validation.py
python test_route_segments.py
python test_station_search.py
```

## Postman Collection

The exported Postman collection is available at:

```text
postman/fuel-route-optimizer.postman_collection.json
```

Import this JSON file into Postman to test the API endpoints.

## Data Files

- `data/fuel-prices-for-be-assessment.csv` — supplied fuel price dataset.
- `data/2026_Gaz_place_national.txt` — US place data used for approximate coordinates.

## Limitations

- Station coordinates are approximate city/place coordinates, not exact fuel pump locations.
- Some stations may not have coordinates.
- Fuel recommendations depend on the supplied dataset and configured vehicle assumptions.
- Public Nominatim and OSRM services are subject to availability and usage policies.
- The optimization algorithm uses a 0.1-mile resolution.

## Notes

This project was developed as a backend coding assessment using Django REST Framework.
