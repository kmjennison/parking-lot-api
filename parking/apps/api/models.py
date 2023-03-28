from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _


class SpotType(models.TextChoices):
    MOTORCYCLE = 'motorcycle', _('motorcycle')
    CAR = 'car', _('car')
    VAN = 'van', _('van')


class VehicleType(models.TextChoices):
    MOTORCYCLE = 'motorcycle', _('motorcycle')
    CAR = 'car', _('car')
    VAN = 'van', _('van')


class ParkingLot(models.Model):
    pass


class Vehicle(models.Model):
    def __str__(self):
        return f'{self.license_plate} - {self.vehicle_type}'

    # Current limitations:
    #  * License plates are not guaranteed unique for cars from different states.
    #  * License plates might be reassigned to different vehicles.
    license_plate = models.CharField(unique=True, max_length=10)
    vehicle_type = models.CharField(choices=VehicleType.choices, max_length=12)

    class Meta:
        ordering = ['pk']


class Spot(models.Model):
    def __str__(self):
        return f'Lot {self.parking_lot_id}, pos {self.pos}'

    class Meta:
        ordering = ['parking_lot_id', 'pos']

    parking_lot = models.ForeignKey(ParkingLot, related_name="spots", related_query_name="spot", db_index=True,
                                    on_delete=models.CASCADE)
    spot_type = models.CharField(db_index=True, choices=SpotType.choices, max_length=12)
    pos = models.PositiveIntegerField(verbose_name="Position in row", help_text="The spot's position in the row.")
    vehicle = models.ForeignKey(Vehicle, null=True, on_delete=models.SET_NULL, related_name='spots',
                                related_query_name='spot')

    # Rationale for tracking unoccupied adjacent spaces: support quicker searches for open blocks of car spots at the
    # expense of write overhead while parking.
    unocc_adj_left = models.PositiveSmallIntegerField(verbose_name="Unoccupied adjacent spots to the left",
                                                      help_text="The number of unoccupied adjacent parking spots to the left of this spot, currently between 0 and 1 (inclusive).",
                                                      default=1)
    unocc_adj_right = models.PositiveSmallIntegerField(verbose_name="Unoccupied adjacent spots to the right", default=1)

    @property
    def occupied(self) -> bool:
        return self.vehicle is not None

    def _get_adjacent_spot(self, pos_diff):
        try:
            spot = Spot.objects.get(parking_lot=self.parking_lot, pos=self.pos + pos_diff)
        except ObjectDoesNotExist:
            spot = None
        return spot

    def get_spot_to_left(self):
        """ Get the spot adjacent and to the left of this spot, or None."""
        return self._get_adjacent_spot(-1)

    def get_spot_to_right(self):
        """ Get the spot adjacent and to the right of this spot, or None."""
        return self._get_adjacent_spot(1)
