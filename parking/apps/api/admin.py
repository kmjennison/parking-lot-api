from django.contrib import admin

from parking.apps.api.models import Vehicle, ParkingLot, Spot


class VehicleAdmin(admin.ModelAdmin):
    list_display = ['license_plate', 'vehicle_type', 'parking_lot', 'spots']

    @staticmethod
    def parking_lot(obj):
        # A vehicle should not be in more than one lot.
        return str(getattr(obj.spots.first(), 'parking_lot_id', ''))

    @staticmethod
    def spots(obj):
        return ", ".join([str(s.pos) for s in obj.spots.all()])


admin.site.register(Vehicle, VehicleAdmin)


class ParkingLotAdmin(admin.ModelAdmin):
    pass


admin.site.register(ParkingLot, ParkingLotAdmin)


class SpotAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'parking_lot_id', 'pos', 'spot_type', 'vehicle', 'occupied']


admin.site.register(Spot, SpotAdmin)
