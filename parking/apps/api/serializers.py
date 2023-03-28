from parking.apps.api.models import Vehicle, Spot, ParkingLot, VehicleType
from rest_framework import serializers, validators


class ParkingLotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ParkingLot
        fields = ['id', 'url']


class SpotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Spot
        fields = ['id', 'url', 'parking_lot', 'spot_type', 'pos', 'vehicle', 'occupied']
        extra_kwargs = {
            'vehicle': {'lookup_field': 'license_plate'},
        }


class VehicleSerializer(serializers.HyperlinkedModelSerializer):

    # Remove validators to support get_or_create (allow duplicate license_plate during validation).
    license_plate = serializers.CharField(validators=[])

    spots = SpotSerializer(many=True, read_only=True, default=[])

    def create(self, validated_data):
        instance, _ = Vehicle.objects.get_or_create(**validated_data)
        return instance

    class Meta:
        model = Vehicle
        fields = ['url', 'license_plate', 'vehicle_type', 'spots']
        extra_kwargs = {
            'url': {'lookup_field': 'license_plate'},
        }


class VehicleParkResponseSerializer(serializers.Serializer):
    # TODO: may be nice to return vehicle and/or parking spots
    # TODO: convert to a class to provide more information, such as an error code.
    error = serializers.CharField(default=None)
    success = serializers.BooleanField()



class VehicleRemoveResponseSerializer(serializers.Serializer):
    # TODO: same improvements as above
    error = serializers.CharField(default=None)
    success = serializers.BooleanField()

