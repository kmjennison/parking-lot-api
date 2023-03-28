from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from parking.apps.api.models import Vehicle, Spot
from parking.apps.api.tests.utils import add_test_domain


class VehicleListTests(APITestCase):
    fixtures = ['parking_lots.json', 'vehicles.json', 'spots.json']

    def test_list_vehicles(self):
        """
        Test listing vehicles.
        """
        num_vehicles_total = Vehicle.objects.count()
        url = reverse('vehicle-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], num_vehicles_total)
        self.assertIsNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        self.assertDictEqual(response.data['results'][0], {
            "url": add_test_domain('/api/vehicles/ABC123/'),
            "license_plate": "ABC123",
            "vehicle_type": "car",
            "spots": []
        })


class VehicleParkTests(APITestCase):
    fixtures = ['parking_lots.json', 'vehicles.json', 'spots.json']

    def test_park_car(self):
        """
        Test parking one car succeeds.
        """
        vehicle = Vehicle.objects.get(vehicle_type='car', license_plate='ABC123')
        url = reverse('vehicle-park', args=[vehicle.license_plate])
        expected_spot = Spot.objects.get(parking_lot=1, pos=2, spot_type="car")
        self.assertIsNone(expected_spot.vehicle)
        response = self.client.post(url, {"parking_lot": 1, "vehicle_type": vehicle.vehicle_type}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_spot.refresh_from_db()
        self.assertEqual(expected_spot.vehicle, vehicle)
        self.assertEqual(Spot.objects.get(parking_lot=1, pos=2).vehicle, Vehicle.objects.get(license_plate='ABC123'))
        self.assertEqual(response.data, {
            "error": None,
            "success": True,
        })

    def test_park_modifies_neighbor_adj_data(self):
        """
        Test that parking a vehicle modifies the adjacent spots' data.
        """
        vehicle = Vehicle.objects.get(vehicle_type='car', license_plate='ABC123')
        url = reverse('vehicle-park', args=[vehicle.license_plate])
        expected_spot = Spot.objects.get(parking_lot=1, pos=2, spot_type="car")
        adjacent_spot_right = Spot.objects.get(parking_lot=1, pos=3)
        self.assertEqual(adjacent_spot_right.unocc_adj_left, 1)
        self.client.post(url, {"parking_lot": 1, "vehicle_type": vehicle.vehicle_type}, format='json')
        expected_spot.refresh_from_db()
        adjacent_spot_right.refresh_from_db()
        self.assertEqual(expected_spot.vehicle, vehicle)
        self.assertEqual(adjacent_spot_right.unocc_adj_left, 0)

    def test_park_motorcycle(self):
        """
        Test parking one motorcycle succeeds.
        """
        vehicle = Vehicle.objects.get(vehicle_type='motorcycle', license_plate='2SLOW')
        self.assertEqual(vehicle.spots.all().count(), 0)
        expected_spot = Spot.objects.get(parking_lot=1, pos=12, spot_type="motorcycle")
        self.assertIsNone(expected_spot.vehicle)
        url = reverse('vehicle-park', args=[vehicle.license_plate])
        response = self.client.post(url, {"parking_lot": 1, "vehicle_type": vehicle.vehicle_type}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_spot.refresh_from_db()
        self.assertEqual(expected_spot.vehicle, vehicle)
        self.assertEqual(response.data, {
            "error": None,
            "success": True,
        })

    def test_park_van(self):
        """
        Test parking one van succeeds.
        """
        vehicle = Vehicle.objects.get(vehicle_type='van', license_plate='IFW32LS')
        self.assertEqual(vehicle.spots.all().count(), 0)
        expected_spot = Spot.objects.get(parking_lot=1, pos=14, spot_type="van")
        self.assertIsNone(expected_spot.vehicle)
        url = reverse('vehicle-park', args=[vehicle.license_plate])
        response = self.client.post(url, {"parking_lot": 1, "vehicle_type": vehicle.vehicle_type}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_spot.refresh_from_db()
        self.assertEqual(expected_spot.vehicle, vehicle)
        self.assertEqual(response.data, {
            "error": None,
            "success": True,
        })

    def test_park_van_in_car_spots(self):
        """
        Test that a van parks in car spots when no van spots are available.
        """
        van_1 = Vehicle.objects.get(vehicle_type='van', license_plate='IFW32LS')
        van_2 = Vehicle.objects.get(vehicle_type='van', license_plate='ASDFG')

        url_1 = reverse('vehicle-park', args=[van_1.license_plate])
        self.client.post(url_1, {"parking_lot": 3, "vehicle_type": van_1.vehicle_type}, format='json')
        self.assertQuerysetEqual(van_1.spots.all(), [Spot.objects.get(parking_lot=3, spot_type="van")])

        url_2 = reverse('vehicle-park', args=[van_2.license_plate])
        response = self.client.post(url_2, {"parking_lot": 3, "vehicle_type": van_2.vehicle_type}, format='json')
        van_2.refresh_from_db()
        expected_spots = Spot.objects.filter(parking_lot=3, pos__gte=2, pos__lte=4, spot_type="car")
        self.assertQuerysetEqual(van_2.spots.all(), expected_spots)
        self.assertEqual(van_2.spots.all().count(), 3)
        self.assertEqual(response.data, {
            "error": None,
            "success": True,
        })

    def test_park_same_vehicle_twice(self):
        """
        Test that it returns an error when trying to park the same vehicle twice.
        """
        vehicle = Vehicle.objects.get(vehicle_type='car', license_plate='ABC123')
        url = reverse('vehicle-park', args=[vehicle.license_plate])
        expected_spot = Spot.objects.get(parking_lot=1, pos=2, spot_type="car")
        self.assertIsNone(expected_spot.vehicle)
        response_1 = self.client.post(url, {"parking_lot": 1, "vehicle_type": vehicle.vehicle_type}, format='json')
        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        response_2 = self.client.post(url, {"parking_lot": 1, "vehicle_type": vehicle.vehicle_type}, format='json')
        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_2.data, {
            "error": "Vehicle is already parked",
            "success": False,
        })

    def test_park_lot_full(self):
        """
        Test parking when the parking lot is full.
        """
        parking_lot_id = 4
        self.assertEqual(Spot.objects.filter(parking_lot_id=parking_lot_id, vehicle__isnull=True).count(), 1)
        response_1 = self.client.post(reverse('vehicle-park', args=['ABC123']),
                                      {"parking_lot": parking_lot_id, "vehicle_type": "car"}, format='json')
        self.assertEqual(response_1.data, {
            "error": None,
            "success": True,
        })
        self.assertEqual(Spot.objects.filter(parking_lot_id=parking_lot_id, vehicle__isnull=True).count(), 0)
        response_2 = self.client.post(reverse('vehicle-park', args=['K321XYZ']),
                                      {"parking_lot": parking_lot_id, "vehicle_type": "car"},
                                      format='json')
        self.assertEqual(response_2.data, {
            "error": "No spots available for this vehicle",
            "success": False,
        })

class VehicleRemoveTests(APITestCase):
    fixtures = ['parking_lots.json', 'vehicles.json', 'spots.json']

    def test_remove_parked_vehicle(self):
        """
        Test removing a parked vehicle.
        """

        # First, park a car.
        vehicle = Vehicle.objects.get(vehicle_type='car', license_plate='ABC123')
        url = reverse('vehicle-park', args=[vehicle.license_plate])
        expected_spot = Spot.objects.get(parking_lot=1, pos=2, spot_type="car")
        self.assertIsNone(expected_spot.vehicle)
        response = self.client.post(url, {"parking_lot": 1, "vehicle_type": vehicle.vehicle_type}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_spot.refresh_from_db()
        self.assertEqual(expected_spot.vehicle, vehicle)
        self.assertEqual(vehicle.spots.all().count(), 1)

        response_2 = self.client.post(reverse('vehicle-remove', args=[vehicle.license_plate]), format='json')
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        expected_spot.refresh_from_db()
        self.assertIsNone(expected_spot.vehicle)
        self.assertEqual(vehicle.spots.all().count(), 0)

    def test_remove_vehicle_modifies_neighbor_adj_data(self):
        """
        Test that removing a parked a vehicle modifies the adjacent spots' data.
        """
        vehicle = Vehicle.objects.get(vehicle_type='car', license_plate='ABC123')
        url = reverse('vehicle-park', args=[vehicle.license_plate])
        expected_spot = Spot.objects.get(parking_lot=1, pos=2, spot_type="car")
        adjacent_spot_right = Spot.objects.get(parking_lot=1, pos=3)
        self.assertEqual(adjacent_spot_right.unocc_adj_left, 1)
        self.client.post(url, {"parking_lot": 1, "vehicle_type": vehicle.vehicle_type}, format='json')
        expected_spot.refresh_from_db()
        adjacent_spot_right.refresh_from_db()
        self.assertEqual(expected_spot.vehicle, vehicle)
        self.assertEqual(adjacent_spot_right.unocc_adj_left, 0)

        self.client.post(reverse('vehicle-remove', args=[vehicle.license_plate]), format='json')
        adjacent_spot_right.refresh_from_db()
        self.assertEqual(adjacent_spot_right.unocc_adj_left, 1)
