"""Repeatable performance benchmark tests (Issue #17, TC-Perf-01).

Requirement:
Overall booking transaction response, from search to confirmation, must be
within 5 seconds for 90% of transactions under normal load.

Acceptance Criteria:
The 90th percentile response time must be <= 5 seconds in the test environment.
"""

from datetime import date, time
from decimal import Decimal
import statistics
import time as pytime
from unittest.mock import patch

from modules import allocation, booking, payment, pnr, search, seat_allocation


class MockBenchmarkRepo:
    """Mock database repository simulating fast query execution."""

    def __init__(self):
        self.schedules = {
            1: {
                "train_id": 1,
                "train_no": "10001",
                "name": "Silicon Express",
                "source": "Bengaluru",
                "destination": "Chennai",
                "departure_time": time(6, 0),
                "arrival_time": time(11, 30),
                "travel_date": date.today(),
                "classes": {"3A": {"fare": Decimal("900.00"), "total_seats": 500}},
            }
        }
        self.bookings = {}
        self.payments = []
        self.next_booking_id = 1

    def search_rows(self, source, destination, travel_date):
        rows = []
        for s_id, s in self.schedules.items():
            if (s["source"].lower() == source.lower()
                    and s["destination"].lower() == destination.lower()
                    and s["travel_date"] == travel_date):
                for code, c in s["classes"].items():
                    rows.append({
                        "train_id": s["train_id"],
                        "train_no": s["train_no"],
                        "name": s["name"],
                        "source": s["source"],
                        "destination": s["destination"],
                        "departure_time": s["departure_time"],
                        "arrival_time": s["arrival_time"],
                        "schedule_id": s_id,
                        "travel_date": s["travel_date"],
                        "class_code": code,
                        "fare": c["fare"],
                        "total_seats": c["total_seats"],
                    })
        return rows

    def get_seat_availability(self, train_id, travel_date, class_code):
        s = self.schedules.get(train_id)
        if not s or s["travel_date"] != travel_date or class_code not in s["classes"]:
            return None
        c = s["classes"][class_code]
        allocated = sum(1 for b in self.bookings.values() if b["status"] == "CONFIRMED")
        return {
            "train_id": s["train_id"],
            "train_no": s["train_no"],
            "train_name": s["name"],
            "travel_date": s["travel_date"],
            "class_code": class_code,
            "total_seats": c["total_seats"],
            "allocated_seats": allocated,
        }

    def get_counts(self, schedule_id, class_code):
        s = self.schedules.get(schedule_id)
        if not s or class_code not in s["classes"]:
            return None
        total = s["classes"][class_code]["total_seats"]
        held = sum(1 for b in self.bookings.values() if b["status"] in {"CONFIRMED", "PROVISIONAL"})
        return {
            "total_seats": total,
            "held_seats": held,
            "rac_count": 0,
            "waitlist_count": 0,
        }

    def create_provisional_booking(self, user_id, schedule_id, class_code,
                                  passenger_name, passenger_age, passenger_gender, berth_preference):
        b_id = self.next_booking_id
        self.next_booking_id += 1
        b = {
            "id": b_id,
            "user_id": user_id,
            "schedule_id": schedule_id,
            "class_code": class_code,
            "passenger_name": passenger_name,
            "passenger_age": passenger_age,
            "passenger_gender": passenger_gender,
            "berth_preference": berth_preference,
            "fare": Decimal("900.00"),
            "status": "PROVISIONAL",
            "pnr": None,
            "allocation_status": "CONFIRMED",
        }
        self.bookings[b_id] = b
        return {"id": b_id, "fare": b["fare"], "held_until": "2026-11-20 12:00:00"}

    def record_payment(self, user_id, booking_id, transaction_ref, status):
        b = self.bookings.get(booking_id)
        if not b or b["user_id"] != user_id:
            raise ValueError("Booking not found.")
        new_status = "CONFIRMED" if status == "SUCCESS" else "CANCELLED"
        b["status"] = new_status
        self.payments.append({"booking_id": booking_id, "status": status, "ref": transaction_ref})
        return {
            "booking_id": booking_id,
            "transaction_ref": transaction_ref,
            "status": status,
            "booking_status": new_status,
            "amount": b["fare"],
            "pnr": None,
        }

    def get_booking(self, booking_id):
        b = self.bookings.get(booking_id)
        if not b:
            return None
        s = self.schedules[b["schedule_id"]]
        return {
            "id": b["id"],
            "user_id": b["user_id"],
            "pnr": b["pnr"],
            "status": b["status"],
            "train_no": s["train_no"],
            "train_name": s["name"],
            "source": s["source"],
            "destination": s["destination"],
            "travel_date": s["travel_date"],
            "departure_time": s["departure_time"],
            "class_code": b["class_code"],
            "passenger_name": b["passenger_name"],
            "fare": b["fare"],
        }

    def pnr_exists(self, pnr_str):
        return any(b["pnr"] == pnr_str for b in self.bookings.values())

    def set_pnr(self, booking_id, pnr_str):
        b = self.bookings.get(booking_id)
        if b and b["status"] == "CONFIRMED":
            b["pnr"] = pnr_str
            return True
        return False

    def get_booking_by_pnr(self, pnr_str):
        for b in self.bookings.values():
            if b["pnr"] == pnr_str:
                return self.get_booking(b["id"])
        return None


def test_booking_transaction_performance_90th_percentile():
    """TC-Perf-01: End-to-end booking transaction response time must be <= 5.0s for 90% of requests."""
    repo = MockBenchmarkRepo()
    num_transactions = 100
    latencies = []

    orig_assign_pnr = pnr.assign_pnr

    def _mock_assign_pnr(b_id, *args, **kwargs):
        return orig_assign_pnr(b_id, repo=repo)

    for i in range(num_transactions):
        start_time = pytime.perf_counter()

        # Step 1: Search trains
        trains, errs = search.search_trains(
            "Bengaluru", "Chennai", str(date.today()), repo=repo
        )
        assert len(trains) > 0

        # Step 2: Check availability
        with patch("modules.allocation.get_seat_availability", side_effect=repo.get_seat_availability):
            avail = allocation.check_availability(1, str(date.today()), "3A")
        assert avail is not None

        # Step 3: Check allocation status
        status_info = seat_allocation.assign_status(1, "3A", repo=repo)
        assert status_info["status"] == "CONFIRMED"

        # Step 4: Create provisional booking
        prov = booking.create_booking(
            user_id=10,
            schedule_id=1,
            class_code="3A",
            passenger_name=f"Passenger {i}",
            passenger_age=30,
            passenger_gender="Male",
            berth_preference="Lower",
            repo=repo,
        )
        assert prov["id"] > 0

        # Step 5: Process payment
        with patch("modules.payment.pnr_module.assign_pnr", side_effect=_mock_assign_pnr):
            pay_result = payment.process_payment(
                user_id=10,
                booking_id=prov["id"],
                payment_outcome="SUCCESS",
                repo=repo,
            )
        assert pay_result["status"] == "SUCCESS"
        assert pay_result["pnr"] is not None

        # Step 6: Lookup confirmed booking
        confirmed_booking = pnr.lookup_pnr(pay_result["pnr"], user_id=10, repo=repo)
        assert confirmed_booking["status"] == "CONFIRMED"

        duration = pytime.perf_counter() - start_time
        latencies.append(duration)

    # Compute statistical metrics
    avg_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    p90_latency = statistics.quantiles(latencies, n=10)[8]  # 90th percentile
    p95_latency = statistics.quantiles(latencies, n=20)[18] # 95th percentile
    max_latency = max(latencies)
    min_latency = min(latencies)

    print("\n--- TC-Perf-01 Benchmark Results ---")
    print(f"Transactions executed: {num_transactions}")
    print(f"Min latency:     {min_latency*1000:.2f} ms")
    print(f"Max latency:     {max_latency*1000:.2f} ms")
    print(f"Average latency: {avg_latency*1000:.2f} ms")
    print(f"Median latency:  {median_latency*1000:.2f} ms")
    print(f"90th percentile: {p90_latency*1000:.2f} ms")
    print(f"95th percentile: {p95_latency*1000:.2f} ms")
    print("Target: 90th percentile <= 5.0 seconds")

    # Assertions for Acceptance Criteria AC-RRS-NF-001
    assert p90_latency <= 5.0, f"90th percentile {p90_latency:.4f}s exceeded 5.0s threshold"
    assert avg_latency <= 5.0, f"Average latency {avg_latency:.4f}s exceeded 5.0s threshold"


def test_payment_failure_workflow_performance():
    """Verify performance of failed payment workflow and seat release."""
    repo = MockBenchmarkRepo()
    latencies = []

    for i in range(50):
        start = pytime.perf_counter()

        prov = booking.create_booking(
            user_id=20,
            schedule_id=1,
            class_code="3A",
            passenger_name=f"Fail Passenger {i}",
            passenger_age=25,
            passenger_gender="Female",
            repo=repo,
        )

        pay_res = payment.process_payment(
            user_id=20,
            booking_id=prov["id"],
            payment_outcome="FAILED",
            repo=repo,
        )
        assert pay_res["status"] == "FAILED"
        assert pay_res["booking_status"] == "CANCELLED"

        latencies.append(pytime.perf_counter() - start)

    p90 = statistics.quantiles(latencies, n=10)[8]
    assert p90 <= 5.0
