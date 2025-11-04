from django.test import TestCase
from rest_framework.test import APIClient

# Create your tests here.


class TripApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_trip_returns_plan_and_logs(self):
        payload = {
            "driver_name": "Test Driver",
            "current_location": "Chicago, IL",
            "pickup_location": "Chicago, IL",
            "dropoff_location": "Dallas, TX",
            "current_cycle_hours": 10,
        }
        resp = self.client.post("/api/v1/trips/", payload, format="json")
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        # Ensure route and logs present
        self.assertIn("plan_json", body)
        self.assertIn("route", body["plan_json"])
        self.assertIn("logs", body["plan_json"])
        self.assertIsInstance(body["plan_json"]["logs"], list)
        # Ensure at least one LogDay created and serialized
        self.assertIn("log_days", body)
        self.assertTrue(len(body["log_days"]) >= 1)
