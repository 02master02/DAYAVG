from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dayavg.services.calculator import calculate_held_days, calculate_item_state, format_currency  # noqa: E402
from dayavg.services.persistence import ImportValidationError, build_export_payload, parse_import_payload  # noqa: E402
from dayavg.services.presentation import classify_item_visual  # noqa: E402
from dayavg.services.validation import FormValidationError, parse_item_form, parse_retirement_form  # noqa: E402
from dayavg.storage.repository import StoredItemRecord  # noqa: E402


class CalculatorServiceTests(unittest.TestCase):
    def test_same_day_purchase_counts_as_one_day(self) -> None:
        today = date(2026, 5, 21)
        self.assertEqual(calculate_held_days(today, today), 1)

    def test_past_purchase_counts_inclusive_days(self) -> None:
        purchase_date = date(2026, 5, 19)
        today = date(2026, 5, 21)
        self.assertEqual(calculate_held_days(purchase_date, today), 3)

    def test_parse_form_computes_daily_cost(self) -> None:
        parsed = parse_item_form(
            {"item_name": "Laptop", "price": "10.00", "purchase_date": "2026-05-19"},
            current_date=date(2026, 5, 21),
        )

        self.assertEqual(parsed.price, Decimal("10.00"))
        self.assertEqual(parsed.held_days, 3)
        self.assertEqual(parsed.daily_cost_cents, 333)
        self.assertEqual(format_currency(parsed.daily_cost_cents), "\u00a53.33")

    def test_future_purchase_date_is_rejected(self) -> None:
        with self.assertRaises(FormValidationError) as context:
            parse_item_form(
                {"item_name": "Laptop", "price": "10.00", "purchase_date": "2026-05-22"},
                current_date=date(2026, 5, 21),
            )

        self.assertIn("purchase_date", context.exception.errors)

    def test_invalid_form_fields_are_rejected(self) -> None:
        with self.assertRaises(FormValidationError) as context:
            parse_item_form(
                {"item_name": "", "price": "-5", "purchase_date": ""},
                current_date=date(2026, 5, 21),
            )

        self.assertIn("item_name", context.exception.errors)
        self.assertIn("price", context.exception.errors)
        self.assertIn("purchase_date", context.exception.errors)

    def test_parse_form_can_validate_against_retirement_date(self) -> None:
        with self.assertRaises(FormValidationError) as context:
            parse_item_form(
                {"item_name": "Laptop", "price": "10.00", "purchase_date": "2026-05-22"},
                current_date=date(2026, 5, 25),
                max_purchase_date=date(2026, 5, 21),
                max_purchase_date_label="退役日期",
            )

        self.assertIn("退役日期", context.exception.errors["purchase_date"])

    def test_retirement_form_accepts_note_and_date(self) -> None:
        parsed = parse_retirement_form(
            {"retired_on": "2026-05-20", "retired_note": "屏幕坏了"},
            purchase_date=date(2026, 5, 18),
            current_date=date(2026, 5, 21),
            price_cents=10000,
        )

        self.assertEqual(parsed.retired_on, date(2026, 5, 20))
        self.assertEqual(parsed.retired_note, "屏幕坏了")
        self.assertEqual(parsed.held_days, 3)

    def test_retirement_form_rejects_date_before_purchase(self) -> None:
        with self.assertRaises(FormValidationError) as context:
            parse_retirement_form(
                {"retired_on": "2026-05-17", "retired_note": ""},
                purchase_date=date(2026, 5, 18),
                current_date=date(2026, 5, 21),
                price_cents=10000,
            )

        self.assertIn("retired_on", context.exception.errors)

    def test_item_state_is_frozen_when_reference_date_stops_moving(self) -> None:
        state = calculate_item_state(10000, date(2026, 5, 20), date(2026, 5, 21))
        self.assertEqual(state["held_days"], 2)
        self.assertEqual(state["daily_cost_cents"], 5000)

    def test_item_visual_classification_uses_specific_icon_when_available(self) -> None:
        phone_visual = classify_item_visual("iPhone 12")
        watch_visual = classify_item_visual("Apple Watch")

        self.assertEqual(phone_visual["icon_filename"], "phone.png")
        self.assertEqual(watch_visual["icon_filename"], "wearable.png")

    def test_item_visual_falls_back_to_office_life_and_other(self) -> None:
        office_visual = classify_item_visual("Logitech mouse")
        life_visual = classify_item_visual("保温杯")
        other_visual = classify_item_visual("收藏摆件")

        self.assertEqual(office_visual["icon_filename"], "office.png")
        self.assertEqual(life_visual["icon_filename"], "life.png")
        self.assertEqual(other_visual["icon_filename"], "other.png")

    def test_export_payload_contains_expected_fields(self) -> None:
        records = [
            StoredItemRecord(
                id=1,
                item_name="Kindle",
                price_cents=90000,
                purchase_date="2026-05-20",
                held_days=2,
                daily_cost_cents=45000,
                created_at="2026-05-21 19:00:00",
                retired_on=None,
                retired_note=None,
            )
        ]

        payload = build_export_payload(records)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["item_name"], "Kindle")
        self.assertNotIn("held_days", payload["items"][0])

    def test_parse_import_payload_accepts_valid_export(self) -> None:
        raw_text = """
        {
          "schema_version": 1,
          "items": [
            {
              "id": 1,
              "item_name": "Kindle",
              "price_cents": 90000,
              "purchase_date": "2026-05-20",
              "created_at": "2026-05-21 19:00:00",
              "retired_on": null,
              "retired_note": null
            }
          ]
        }
        """

        items = parse_import_payload(raw_text, current_date=date(2026, 5, 21))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["held_days"], 2)
        self.assertEqual(items[0]["daily_cost_cents"], 45000)

    def test_parse_import_payload_rejects_invalid_schema(self) -> None:
        with self.assertRaises(ImportValidationError):
            parse_import_payload('{"schema_version": 2, "items": []}', current_date=date(2026, 5, 21))

    def test_parse_import_payload_rejects_duplicate_ids(self) -> None:
        raw_text = """
        {
          "schema_version": 1,
          "items": [
            {
              "id": 1,
              "item_name": "A",
              "price_cents": 100,
              "purchase_date": "2026-05-20",
              "created_at": "2026-05-21 19:00:00",
              "retired_on": null,
              "retired_note": null
            },
            {
              "id": 1,
              "item_name": "B",
              "price_cents": 100,
              "purchase_date": "2026-05-20",
              "created_at": "2026-05-21 19:01:00",
              "retired_on": null,
              "retired_note": null
            }
          ]
        }
        """

        with self.assertRaises(ImportValidationError):
            parse_import_payload(raw_text, current_date=date(2026, 5, 21))


if __name__ == "__main__":
    unittest.main()
