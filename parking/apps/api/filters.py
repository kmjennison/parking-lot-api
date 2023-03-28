import django_filters

from parking.apps.api.models import Vehicle, VehicleType, VehicleType


class SpotFilter(django_filters.FilterSet):
    occupied = django_filters.BooleanFilter(field_name='vehicle', lookup_expr='isnull', exclude=True)
    vehicleType = django_filters.MultipleChoiceFilter(field_name='vehicle__vehicle_type', choices=VehicleType.choices)
