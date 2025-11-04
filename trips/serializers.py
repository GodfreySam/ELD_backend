from rest_framework import serializers

from .models import LogDay, Trip


class LogDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogDay
        fields = ['id', 'date', 'segments_json']


class TripSerializer(serializers.ModelSerializer):
    log_days = LogDaySerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id',
            'driver_name',
            'created_at',
            'current_location',
            'pickup_location',
            'dropoff_location',
            'current_cycle_hours',
            'plan_json',
            'log_days',
        ]
