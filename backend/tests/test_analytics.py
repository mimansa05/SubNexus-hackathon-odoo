import unittest
from datetime import datetime, timezone
from decimal import Decimal

from app.services.analytics_service import (
    _event_status,
    _period_dates,
    monthly_recurring_amount,
)


class MonthlyRecurringAmountTests(unittest.TestCase):
    def test_normalizes_billing_intervals(self):
        self.assertEqual(
            monthly_recurring_amount(Decimal("120.00"), "monthly", 1),
            Decimal("120.00"),
        )
        self.assertEqual(
            monthly_recurring_amount(Decimal("120.00"), "yearly", 1),
            Decimal("10.00"),
        )
        self.assertEqual(
            monthly_recurring_amount(Decimal("10.00"), "weekly", 1),
            Decimal("43.33"),
        )
        self.assertEqual(
            monthly_recurring_amount(Decimal("3.65"), "daily", 1),
            Decimal("111.02"),
        )

    def test_interval_count_divides_monthly_equivalent(self):
        self.assertEqual(
            monthly_recurring_amount(Decimal("240.00"), "monthly", 2),
            Decimal("120.00"),
        )
        self.assertEqual(
            monthly_recurring_amount(Decimal("240.00"), "yearly", 2),
            Decimal("10.00"),
        )

    def test_rejects_invalid_interval(self):
        with self.assertRaises(ValueError):
            monthly_recurring_amount(Decimal("10.00"), "hourly", 1)
        with self.assertRaises(ValueError):
            monthly_recurring_amount(Decimal("10.00"), "monthly", 0)


class ChurnPeriodTests(unittest.TestCase):
    def test_period_boundaries_are_utc_calendar_periods(self):
        now = datetime(2026, 10, 31, 13, 30, tzinfo=timezone.utc)
        month_start, month_end = _period_dates("month", now)
        quarter_start, _ = _period_dates("quarter", now)
        year_start, _ = _period_dates("year", now)
        self.assertEqual(month_start, datetime(2026, 10, 1, tzinfo=timezone.utc))
        self.assertEqual(quarter_start, datetime(2026, 10, 1, tzinfo=timezone.utc))
        self.assertEqual(year_start, datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(month_end, now)

    def test_subscription_event_status_mapping(self):
        self.assertEqual(_event_status("created", {"status": "trialing"}), "trialing")
        self.assertEqual(_event_status("activated", None), "active")
        self.assertEqual(_event_status("paused", None), "paused")
        self.assertEqual(_event_status("canceled", None), "canceled")
        self.assertIsNone(_event_status("cancellation_scheduled", None))


if __name__ == "__main__":
    unittest.main()
