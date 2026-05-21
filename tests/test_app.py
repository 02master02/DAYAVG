from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import create_app  # noqa: E402


class DayAvgAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test_dayavg.db"
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE_PATH": str(database_path),
                "TODAY_OVERRIDE": date(2026, 5, 21),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_index_page_renders_dashboard_sections(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("资产日均观察", body)
        self.assertIn("总物品价值", body)
        self.assertIn("资产列表", body)

    def test_valid_submission_redirects_and_is_shown_in_history(self) -> None:
        response = self.client.post(
            "/items",
            data={
                "item_name": "Kindle",
                "price": "900.00",
                "purchase_date": "2026-05-20",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Kindle", body)
        self.assertIn("\u00a5900.00", body)
        self.assertIn("\u00a5450.00", body)
        self.assertIn("2天", body)
        self.assertIn("平板", body)
        self.assertIn("icons/tablet.png", body)

    def test_active_item_updates_when_today_moves_forward(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "iPhone 12", "price": "100.00", "purchase_date": "2026-05-20"},
        )
        self.app.config["TODAY_OVERRIDE"] = date(2026, 5, 25)

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertIn("6天", body)
        self.assertIn("\u00a516.67", body)

    def test_invalid_submission_shows_validation_error(self) -> None:
        response = self.client.post(
            "/items",
            data={
                "item_name": "",
                "price": "0",
                "purchase_date": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("请输入物品名称", body)
        self.assertIn("购买价格必须大于 0", body)
        self.assertIn("请输入购买日期", body)

    def test_summary_metrics_aggregate_multiple_items(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "iPhone 12", "price": "100.00", "purchase_date": "2026-05-20"},
        )
        response = self.client.post(
            "/items",
            data={"item_name": "MacBook Pro", "price": "300.00", "purchase_date": "2026-05-19"},
            follow_redirects=True,
        )

        body = response.get_data(as_text=True)
        self.assertIn("\u00a5400.00", body)
        self.assertIn("\u00a5200.00", body)
        self.assertIn("使用中", body)

    def test_edit_form_is_shown_for_selected_item(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "MacBook Pro", "price": "300.00", "purchase_date": "2026-05-19"},
        )

        response = self.client.get("/?editing_id=1")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("保存修改", body)
        self.assertIn("修改 MacBook Pro", body)

    def test_edit_submission_updates_price_and_purchase_date(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "MacBook Pro", "price": "300.00", "purchase_date": "2026-05-19"},
        )

        response = self.client.post(
            "/items/1/edit",
            data={"price": "600.00", "purchase_date": "2026-05-20"},
            follow_redirects=True,
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("记录已更新", body)
        self.assertIn("\u00a5600.00", body)
        self.assertIn("\u00a5300.00", body)
        self.assertIn("2026-05-20", body)

    def test_invalid_edit_keeps_user_in_edit_mode(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "MacBook Pro", "price": "300.00", "purchase_date": "2026-05-19"},
        )

        response = self.client.post(
            "/items/1/edit",
            data={"price": "0", "purchase_date": ""},
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("保存修改", body)
        self.assertIn("购买价格必须大于 0", body)
        self.assertIn("请输入购买日期", body)

    def test_retirement_settings_form_is_shown_for_selected_item(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "iPhone 12", "price": "100.00", "purchase_date": "2026-05-20"},
        )

        response = self.client.get("/?retiring_id=1")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("保存退役设置", body)
        self.assertIn("退役备注", body)

    def test_retired_item_freezes_after_manual_retirement_date(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "iPhone 12", "price": "100.00", "purchase_date": "2026-05-15"},
        )
        self.client.post(
            "/items/1/retirement",
            data={"action": "retire", "retired_on": "2026-05-18", "retired_note": "屏幕坏了"},
            follow_redirects=True,
        )
        self.app.config["TODAY_OVERRIDE"] = date(2026, 5, 25)

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertIn("已退役", body)
        self.assertIn("冻结于 2026-05-18 · 屏幕坏了", body)
        self.assertIn("\u00a525.00", body)
        self.assertIn("4天", body)

    def test_invalid_retirement_setting_keeps_user_in_retirement_form(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "iPhone 12", "price": "100.00", "purchase_date": "2026-05-20"},
        )

        response = self.client.post(
            "/items/1/retirement",
            data={"action": "retire", "retired_on": "2026-05-19", "retired_note": ""},
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("保存退役设置", body)
        self.assertIn("退役日期不能早于购买日期", body)

    def test_restore_item_clears_retirement_note_and_resumes_updates(self) -> None:
        self.client.post(
            "/items",
            data={"item_name": "iPhone 12", "price": "100.00", "purchase_date": "2026-05-15"},
        )
        self.client.post(
            "/items/1/retirement",
            data={"action": "retire", "retired_on": "2026-05-18", "retired_note": "屏幕坏了"},
        )
        self.client.post("/items/1/retirement", data={"action": "restore"})
        self.app.config["TODAY_OVERRIDE"] = date(2026, 5, 25)

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertIn("使用中", body)
        self.assertIn("按今天实时更新", body)
        self.assertNotIn("屏幕坏了", body)
        self.assertIn("\u00a59.09", body)
        self.assertIn("11天", body)


if __name__ == "__main__":
    unittest.main()
