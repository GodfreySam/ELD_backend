from django.db import models


class Trip(models.Model):
    driver_name = models.CharField(max_length=255, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_hours = models.FloatField()
    plan_json = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Trip {self.id} {self.pickup_location} → {self.dropoff_location}"


class LogDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='log_days')
    date = models.DateField()
    segments_json = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ('trip', 'date')

    def __str__(self) -> str:
        return f"LogDay {self.trip_id} {self.date}"

# Create your models here.
