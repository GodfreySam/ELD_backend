from datetime import date

from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import LogDay, Trip
from .planner import CITY_TO_COORD, plan_trip
from .serializers import TripSerializer


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by('-created_at')
    serializer_class = TripSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trip = serializer.save()
        plan = plan_trip(
            current_location=trip.current_location,
            pickup_location=trip.pickup_location,
            dropoff_location=trip.dropoff_location,
            current_cycle_hours=trip.current_cycle_hours,
            start_date=date.today(),
        )

        # Persist all planned log days for serializer consumption in UI
        for day in plan.logs:
            LogDay.objects.update_or_create(
                trip=trip,
                date=date.fromisoformat(day["date"]),
                defaults={"segments_json": day["segments"]},
            )

        trip.plan_json = {
            "route": {
                "polyline": plan.polyline,
                "distanceMiles": plan.distance_miles,
                "durationHours": plan.duration_hours,
                "stops": plan.stops,
            },
            "logs": plan.logs,
        }
        trip.save(update_fields=["plan_json"])
        headers = self.get_success_headers(serializer.data)
        return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED, headers=headers)


@api_view(['GET'])
def cities_list(request):
    """Return list of available cities with coordinates."""
    cities = [
        {"name": city, "lat": coord[0], "lng": coord[1]}
        for city, coord in sorted(CITY_TO_COORD.items())
    ]
    return Response(cities)
