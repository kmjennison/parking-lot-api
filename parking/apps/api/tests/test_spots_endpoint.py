from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from parking.apps.api.models import Vehicle
from parking.apps.api.tests.utils import add_test_domain


class SpotTests(APITestCase):
    fixtures = ['parking_lots.json', 'vehicles.json', 'spots.json']

    def test_get_spot(self):
        """
        Test getting a spot.
        """
        url = reverse('spot-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, {
          "id": 1,
          "url": add_test_domain('/api/spots/1/'),
          "parking_lot": add_test_domain('/api/parking-lots/1/'),
          "spot_type": "car",
          "pos": 1,
          "vehicle": add_test_domain('/api/vehicles/DEF456/'),
          "occupied": True,
        })


    # TODO: test other methods


class ParkingLotSpotTests(APITestCase):
    fixtures = ['parking_lots.json', 'vehicles.json', 'spots.json']

    def test_get_spots_by_vehicle_type(self):
        """
        Test getting a count of spots by vehicle type.
        """
        url = reverse('parking-lot-spots-list', args=[1])
        response_1 = self.client.get(f'{url}?vehicleType=van', format='json')
        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_1.data['count'], 1)

        # Park another van
        vehicle = Vehicle.objects.get(vehicle_type='van', license_plate='IFW32LS')
        url_park = reverse('vehicle-park', args=[vehicle.license_plate])
        self.client.post(url_park, { "parking_lot": 1, "vehicle_type": vehicle.vehicle_type }, format='json')

        response_2 = self.client.get(f'{url}?vehicleType=van', format='json')
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_2.data['count'], 2)

    def test_get_spots_unoccupied(self):
        """
        Test getting a count of unoccupied spots.
        """
        url = reverse('parking-lot-spots-list', args=[1])
        count_url = f'{url}?occupied=false'
        response_1 = self.client.get(count_url, format='json')
        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_1.data['count'], 11)

        # Park another car
        vehicle = Vehicle.objects.get(vehicle_type='car', license_plate='ABC123')
        url_park = reverse('vehicle-park', args=[vehicle.license_plate])
        self.client.post(url_park, { "parking_lot": 1, "vehicle_type": vehicle.vehicle_type }, format='json')

        response_2 = self.client.get(count_url, format='json')
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_2.data['count'], 10)

    # TODO: test other methods
