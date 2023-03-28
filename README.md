# parking-lot-api

## Get Started

Ensure [Poetry](https://python-poetry.org/) is installed.

Then, in the root directory, install dependencies, set up the SQLite database, and load fixtures data:
```
poetry install
poetry shell
python manage.py migrate
python manage.py loaddata vehicles.json parking_lots.json spots.json
```

Run the app:
```
python manage.py runserver
```

## Documentation

#### Docs
* API docs: http://localhost:8000/api/schema/swagger-ui/
* Browsable data: http://localhost:8000/api/

#### Key Endpoints
- Tell us how many spots are remaining:
  - `/api/parking-lots/1/spots/?occupied=false`
  - Rely on the `count` field
- Tell us when the parking lot is full:
  - `/api/parking-lots/1/spots/?occupied=false`
  - Full if `count` is zero
- Tell us how many spots vans are taking up
  - `/api/parking-lots/1/spots/?vehicleType=van`
- Take in a vehicle to park
  - `/api/vehicles/{license_plate}/park/`
  - In POST data, include: `parking_lot` ID (int) and `vehicle_type` ("car", "motorcycle", or "van")
  - Does not require creating the vehicle prior to parking
- Remove a vehicle from the lot
  - `/api/vehicles/{license_plate}/remove/`


## Test

In the Poetry shell, run:
```
python manage.py test
```
