from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from parking.apps.api.tests.utils import add_test_domain


class ParkingLotTests(APITestCase):
    fixtures = ['parking_lots.json', 'vehicles.json', 'spots.json']

    def test_get_parking_lot(self):
        """
        Test getting a parking lot.
        """
        url = reverse('parkinglot-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, {
          "id": 1,
          "url": add_test_domain('/api/parking-lots/1/')
        })

    # TODO: test other methods
