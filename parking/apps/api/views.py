from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

from parking.apps.api.filters import SpotFilter
from parking.apps.api.models import Vehicle, Spot, ParkingLot, VehicleType, SpotType
from parking.apps.api.serializers import VehicleSerializer, SpotSerializer, ParkingLotSerializer, \
    VehicleParkResponseSerializer, VehicleRemoveResponseSerializer


class ParkingLotViewSet(viewsets.ModelViewSet):
    queryset = ParkingLot.objects.all()
    serializer_class = ParkingLotSerializer


class SpotViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        qs = Spot.objects.all()

        # Handle nested calls; ex: /api/parking-lot/2/spots/
        parking_lot_id = self.kwargs.get('parking_lot_pk', None)
        if parking_lot_id:
            qs = qs.filter(parking_lot=parking_lot_id)
        return qs

    serializer_class = SpotSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SpotFilter
    filterset_fields = ['occupied']


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    lookup_field = 'license_plate'

    @staticmethod
    def _assign_spot(spot, vehicle=None):
        """Assign a vehicle (or unassign, if vehicle is None) to a spot."""
        if not spot:
            return

        spot.vehicle = vehicle
        spot.save()

        # Modify "unoccupied adjacent spots" data for neighboring spots.
        unocc_count = 0 if vehicle else 1
        left_spot = spot.get_spot_to_left()
        right_spot = spot.get_spot_to_right()
        if left_spot:
            left_spot.unocc_adj_right = unocc_count
            left_spot.save()
        if right_spot:
            right_spot.unocc_adj_left = unocc_count
            right_spot.save()

    def _assign_spots(self, spots, vehicle):
        for spot in spots:
            self._assign_spot(spot, vehicle)

    def _determine_spots(self, parking_lot_id, vehicle_type):
        """ Return list of spots to park, or an empty list if no match is found. Multiple spots
            represent adjacent spots that will be occupied by the vehicle.
        """
        qs = Spot.objects.filter(parking_lot_id=parking_lot_id, vehicle__isnull=True)
        spot = None
        if vehicle_type == VehicleType.MOTORCYCLE:
            spot = qs.filter(spot_type=SpotType.MOTORCYCLE).first()

        # Check for car spots 1) for cars, or 2) for motorcycles that did not find a
        # motorcycle spot.
        if vehicle_type == VehicleType.CAR or spot is None:
            spot = qs.filter(spot_type=SpotType.CAR).first()

        if vehicle_type == VehicleType.VAN or spot is None:
            spot = qs.filter(spot_type=SpotType.VAN).first()

        if spot:
            spots = [spot]
        elif vehicle_type == VehicleType.VAN:
            # Special case for vans: if there are no van spots, try to find a car spot that has
            # at least one unoccupied adjacent spot on either side.
            spot = qs.filter(spot_type=SpotType.CAR, unocc_adj_left__gte=1, unocc_adj_right__gte=1).first()
            if spot:
                spots = [spot.get_spot_to_left(), spot, spot.get_spot_to_right()]
        else:
            spots = []

        return spots

    @action(detail=True, methods=['post'])
    def park(self, request, license_plate):
        """ Given vehicle info and a parking lot, attempt to park the vehicle. """
        parking_lot_id = request.data.get('parking_lot', None)

        try:
            ParkingLot.objects.get(id=parking_lot_id)
        except ObjectDoesNotExist:
            raise ValidationError('Parking lot does not exist')

        # Validate input data.
        vehicle_info = VehicleSerializer(data={
            "license_plate": license_plate,
            "vehicle_type": request.data.get('vehicle_type'),
            "spots": []
        })
        vehicle_info.is_valid(raise_exception=True)
        vehicle = vehicle_info.create(vehicle_info.validated_data)

        # Make sure the vehicle isn't already parked.
        if vehicle.spots.all().count() > 0:
            resp = VehicleParkResponseSerializer(data={
                "success": False,
                "error": 'Vehicle is already parked',
            }, context={'request': request})
            resp.is_valid(raise_exception=True)
            return Response(resp.data, status=status.HTTP_400_BAD_REQUEST)

        # Try to park the vehicle.
        spots = self._determine_spots(parking_lot_id, vehicle.vehicle_type)
        if not len(spots):
            resp = VehicleParkResponseSerializer(data={
                "success": False,
                "error": 'No spots available for this vehicle',
            }, context={'request': request})
        else:
            self._assign_spots(spots, vehicle)
            resp = VehicleParkResponseSerializer(data={
                "success": True,
            }, context={'request': request})
        resp.is_valid(raise_exception=True)

        return Response(resp.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def remove(self, request, license_plate):
        """ Given a vehicle identifier, remove the vehicle from its parking spot. """

        def vehicle_not_parked():
            resp = VehicleRemoveResponseSerializer(data={
                "success": False,
                "error": 'Vehicle is not parked',
            }, context={'request': request})
            resp.is_valid(raise_exception=True)
            return Response(resp.data, status=status.HTTP_400_BAD_REQUEST)

        try:
            vehicle = Vehicle.objects.get(license_plate=license_plate)
        except ObjectDoesNotExist:
            return vehicle_not_parked()

        # Make sure the vehicle isn't already parked.
        if vehicle.spots.all().count() < 1:
            return vehicle_not_parked()

        # Passing None for vehicle will unset the spots.
        self._assign_spots(vehicle.spots.all(), vehicle=None)

        resp = VehicleParkResponseSerializer(data={
            "success": True,
        }, context={'request': request})
        resp.is_valid(raise_exception=True)
        return Response(resp.data, status=status.HTTP_200_OK)
