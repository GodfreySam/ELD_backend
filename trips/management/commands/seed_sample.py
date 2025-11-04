from datetime import date

from django.core.management.base import BaseCommand
from trips.models import LogDay, Trip
from trips.planner import plan_trip


class Command(BaseCommand):
    help = "Seed sample Trip and LogDay data"

    def handle(self, *args, **options):
        trip = Trip.objects.create(
            driver_name="Jane Doe",
            current_location="Chicago, IL",
            pickup_location="Denver, CO",
            dropoff_location="Dallas, TX",
            current_cycle_hours=10,
            plan_json={},
        )

        plan = plan_trip(
            current_location=trip.current_location,
            pickup_location=trip.pickup_location,
            dropoff_location=trip.dropoff_location,
            current_cycle_hours=trip.current_cycle_hours,
            start_date=date.today(),
        )

        # Persist all planned days
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

        self.stdout.write(self.style.SUCCESS(f"Seeded sample trip id={trip.id}"))
