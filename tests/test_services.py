from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dayavg.services.calculator import calculate_held_days, calculate_item_state, format_currency  # noqa: E402
from dayavg.services.persistence import ImportValidationError, build_export_payload, parse_import_payload  # noqa: E402
from dayavg.services.presentation import classify_item_visual, get_category_options  # noqa: E402
from dayavg.services.validation import FormValidationError, parse_item_form, parse_retirement_form  # noqa: E402
from dayavg.storage.repository import StoredItemRecord  # noqa: E402


class CalculatorServiceTests(unittest.TestCase):
    def test_same_day_purchase_counts_as_one_day(self) -> None:
        today = date(2026, 5, 21)
        self.assertEqual(calculate_held_days(today, today), 1)

    def test_active_item_state_uses_full_purchase_price(self) -> None:
        state = calculate_item_state(10000, date(2026, 5, 20), date(2026, 5, 21))

        self.assertEqual(state["held_days"], 2)
        self.assertEqual(state["actual_cost_cents"], 10000)
        self.assertEqual(state["daily_cost_cents"], 5000)

    def test_retired_item_state_uses_actual_cost_after_resale(self) -> None:
        state = calculate_item_state(
            10000,
            date(2026, 5, 15),
            date(2026, 5, 18),
            resale_price_cents=4000,
        )

        self.assertEqual(state["held_days"], 4)
        self.assertEqual(state["actual_cost_cents"], 6000)
        self.assertEqual(state["daily_cost_cents"], 1500)
        self.assertEqual(format_currency(state["daily_cost_cents"]), "\u00a515.00")

    def test_parse_item_form_supports_category_and_note(self) -> None:
        parsed = parse_item_form(
            {
                "item_name": "Laptop",
                "category_key": "computer",
                "price": "10.00",
                "purchase_date": "2026-05-19",
                "item_note": "办公主机",
            },
            current_date=date(2026, 5, 21),
        )

        self.assertEqual(parsed.category_key, "computer")
        self.assertEqual(parsed.item_note, "办公主机")
        self.assertEqual(parsed.price, Decimal("10.00"))
        self.assertEqual(parsed.held_days, 3)
        self.assertEqual(parsed.daily_cost_cents, 333)

    def test_future_purchase_date_is_rejected(self) -> None:
        with self.assertRaises(FormValidationError) as context:
            parse_item_form(
                {
                    "item_name": "Laptop",
                    "category_key": "computer",
                    "price": "10.00",
                    "purchase_date": "2026-05-22",
                    "item_note": "",
                },
                current_date=date(2026, 5, 21),
            )

        self.assertIn("purchase_date", context.exception.errors)

    def test_item_note_too_long_is_rejected(self) -> None:
        with self.assertRaises(FormValidationError) as context:
            parse_item_form(
                {
                    "item_name": "Laptop",
                    "category_key": "computer",
                    "price": "10.00",
                    "purchase_date": "2026-05-21",
                    "item_note": "a" * 301,
                },
                current_date=date(2026, 5, 21),
            )

        self.assertIn("item_note", context.exception.errors)

    def test_parse_form_can_validate_against_retirement_date(self) -> None:
        with self.assertRaises(FormValidationError) as context:
            parse_item_form(
                {
                    "item_name": "Laptop",
                    "category_key": "computer",
                    "price": "10.00",
                    "purchase_date": "2026-05-22",
                    "item_note": "",
                },
                current_date=date(2026, 5, 25),
                max_purchase_date=date(2026, 5, 21),
                max_purchase_date_label="退役日期",
            )

        self.assertIn("退役日期", context.exception.errors["purchase_date"])

    def test_retirement_form_accepts_reason_note_and_resale_price(self) -> None:
        parsed = parse_retirement_form(
            {
                "retired_on": "2026-05-20",
                "retired_reason": "升级换代",
                "resale_price": "40.00",
                "retired_note": "同城卖出",
            },
            purchase_date=date(2026, 5, 18),
            current_date=date(2026, 5, 21),
            price_cents=10000,
        )

        self.assertEqual(parsed.retired_on, date(2026, 5, 20))
        self.assertEqual(parsed.retired_reason, "升级换代")
        self.assertEqual(parsed.resale_price, Decimal("40.00"))
        self.assertEqual(parsed.resale_price_cents, 4000)
        self.assertEqual(parsed.held_days, 3)
        self.assertEqual(parsed.actual_cost_cents, 6000)
        self.assertEqual(parsed.daily_cost_cents, 2000)

    def test_retirement_form_rejects_resale_price_above_purchase_price(self) -> None:
        with self.assertRaises(FormValidationError) as context:
            parse_retirement_form(
                {
                    "retired_on": "2026-05-20",
                    "retired_reason": "升级换代",
                    "resale_price": "101.00",
                    "retired_note": "",
                },
                purchase_date=date(2026, 5, 18),
                current_date=date(2026, 5, 21),
                price_cents=10000,
            )

        self.assertIn("resale_price", context.exception.errors)

    def test_manual_category_overrides_name_in_visual_classification(self) -> None:
        visual = classify_item_visual("iPhone 12", "office")
        options = get_category_options()

        self.assertEqual(visual["icon_filename"], "office.png")
        self.assertEqual(visual["category_label"], "办公用品")
        self.assertTrue(any(option["key"] == "office" for option in options))

    def test_export_payload_contains_new_asset_fields(self) -> None:
        records = [
            StoredItemRecord(
                id=1,
                item_name="Kindle",
                category_key="tablet",
                price_cents=90000,
                purchase_date="2026-05-20",
                item_note="阅读器",
                held_days=2,
                daily_cost_cents=45000,
                created_at="2026-05-21 19:00:00",
                retired_on="2026-05-21",
                retired_reason="升级换代",
                resale_price_cents=10000,
                retired_note="已卖出",
            )
        ]

        payload = build_export_payload(records)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["items"][0]["category_key"], "tablet")
        self.assertEqual(payload["items"][0]["item_note"], "阅读器")
        self.assertEqual(payload["items"][0]["retired_reason"], "升级换代")
        self.assertEqual(payload["items"][0]["resale_price_cents"], 10000)
        self.assertNotIn("held_days", payload["items"][0])

    def test_parse_import_payload_accepts_current_export_shape(self) -> None:
        raw_text = """
        {
          "schema_version": 1,
          "items": [
            {
              "id": 1,
              "item_name": "Kindle",
              "category_key": "tablet",
              "price_cents": 90000,
              "purchase_date": "2026-05-18",
              "item_note": "阅读器",
              "created_at": "2026-05-21 19:00:00",
              "retired_on": "2026-05-20",
              "retired_reason": "升级换代",
              "resale_price_cents": 30000,
              "retired_note": "已卖出"
            }
          ]
        }
        """

        items = parse_import_payload(raw_text, current_date=date(2026, 5, 21))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["category_key"], "tablet")
        self.assertEqual(items[0]["item_note"], "阅读器")
        self.assertEqual(items[0]["retired_reason"], "升级换代")
        self.assertEqual(items[0]["resale_price_cents"], 30000)
        self.assertEqual(items[0]["held_days"], 3)
        self.assertEqual(items[0]["daily_cost_cents"], 20000)

    def test_parse_import_payload_accepts_legacy_export_shape(self) -> None:
        raw_text = """
        {
          "schema_version": 1,
          "items": [
            {
              "id": 1,
              "item_name": "Legacy Kindle",
              "price_cents": 90000,
              "purchase_date": "2026-05-20",
              "created_at": "2026-05-21 19:00:00",
              "retired_on": "2026-05-21",
              "retired_note": "旧版备注"
            }
          ]
        }
        """

        items = parse_import_payload(raw_text, current_date=date(2026, 5, 21))

        self.assertEqual(items[0]["category_key"], "tablet")
        self.assertEqual(items[0]["retired_reason"], "旧版备注")
        self.assertEqual(items[0]["retired_note"], "旧版备注")

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
