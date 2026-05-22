from __future__ import annotations

import io
import json
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

    def _create_item(
        self,
        *,
        item_name: str = "Kindle",
        category_key: str = "tablet",
        price: str = "900.00",
        purchase_date: str = "2026-05-20",
        item_note: str = "阅读器",
    ) -> None:
        self.client.post(
            "/items",
            data={
                "item_name": item_name,
                "category_key": category_key,
                "price": price,
                "purchase_date": purchase_date,
                "item_note": item_note,
            },
        )

    def test_index_page_renders_dashboard_sections(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("资产日均观察", body)
        self.assertIn("总物品价值", body)
        self.assertIn("资产列表", body)

    def test_index_includes_local_storage_snapshot_script(self) -> None:
        self._create_item()

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertIn('id="asset-snapshot"', body)
        self.assertIn('"category_key"', body)
        self.assertIn("persistence.js", body)

    def test_valid_submission_stores_category_and_note(self) -> None:
        response = self.client.post(
            "/items",
            data={
                "item_name": "Kindle",
                "category_key": "tablet",
                "price": "900.00",
                "purchase_date": "2026-05-20",
                "item_note": "卧室阅读器",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Kindle", body)
        self.assertIn("平板", body)
        self.assertIn("卧室阅读器", body)
        self.assertIn("\u00a5900.00", body)
        self.assertIn("\u00a5450.00", body)
        self.assertIn("2天", body)

    def test_active_item_updates_when_today_moves_forward(self) -> None:
        self._create_item(item_name="iPhone 12", category_key="phone", price="100.00")
        self.app.config["TODAY_OVERRIDE"] = date(2026, 5, 25)

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertIn("6天", body)
        self.assertIn("\u00a516.67", body)
        self.assertIn("使用中", body)

    def test_edit_submission_updates_name_category_price_date_and_note(self) -> None:
        self._create_item(item_name="MacBook Pro", category_key="computer", price="300.00", purchase_date="2026-05-19")

        response = self.client.post(
            "/items/1/edit",
            data={
                "item_name": "办公鼠标",
                "category_key": "office",
                "price": "600.00",
                "purchase_date": "2026-05-20",
                "item_note": "已换到工位 B",
            },
            follow_redirects=True,
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("记录已更新", body)
        self.assertIn("办公鼠标", body)
        self.assertIn("办公用品", body)
        self.assertIn("已换到工位 B", body)
        self.assertIn("\u00a5600.00", body)
        self.assertIn("\u00a5300.00", body)
        self.assertIn("2026-05-20", body)

    def test_invalid_edit_keeps_user_in_edit_mode(self) -> None:
        self._create_item(item_name="MacBook Pro", category_key="computer", price="300.00", purchase_date="2026-05-19")

        response = self.client.post(
            "/items/1/edit",
            data={
                "item_name": "",
                "category_key": "computer",
                "price": "0",
                "purchase_date": "",
                "item_note": "",
            },
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("保存修改", body)
        self.assertIn("请输入物品名称", body)

    def test_retired_item_freezes_days_and_uses_resale_price_in_daily_cost(self) -> None:
        self._create_item(item_name="iPhone 12", category_key="phone", price="100.00", purchase_date="2026-05-15")
        self.client.post(
            "/items/1/retirement",
            data={
                "action": "retire",
                "retired_on": "2026-05-18",
                "retired_reason": "升级换代",
                "resale_price": "40.00",
                "retired_note": "同城卖出",
            },
            follow_redirects=True,
        )
        self.app.config["TODAY_OVERRIDE"] = date(2026, 5, 25)

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertIn("已退役", body)
        self.assertIn("冻结于 2026-05-18", body)
        self.assertIn("原因：升级换代", body)
        self.assertIn("卖出价 \u00a540.00", body)
        self.assertIn("实际成本 \u00a560.00", body)
        self.assertIn("\u00a515.00", body)
        self.assertIn("4天", body)

    def test_invalid_retirement_setting_keeps_user_in_retirement_form(self) -> None:
        self._create_item(item_name="iPhone 12", category_key="phone", price="100.00", purchase_date="2026-05-20")

        response = self.client.post(
            "/items/1/retirement",
            data={
                "action": "retire",
                "retired_on": "2026-05-19",
                "retired_reason": "",
                "resale_price": "120.00",
                "retired_note": "",
            },
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("保存退役设置", body)
        self.assertIn("请输入退役原因", body)

    def test_restore_item_clears_retirement_fields_and_resumes_updates(self) -> None:
        self._create_item(item_name="iPhone 12", category_key="phone", price="100.00", purchase_date="2026-05-15")
        self.client.post(
            "/items/1/retirement",
            data={
                "action": "retire",
                "retired_on": "2026-05-18",
                "retired_reason": "升级换代",
                "resale_price": "40.00",
                "retired_note": "同城卖出",
            },
        )
        self.client.post("/items/1/retirement", data={"action": "restore"})
        self.app.config["TODAY_OVERRIDE"] = date(2026, 5, 25)

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertIn("使用中", body)
        self.assertIn("按今天实时更新", body)
        self.assertNotIn("同城卖出", body)
        self.assertNotIn("升级换代", body)
        self.assertIn("\u00a59.09", body)
        self.assertIn("11天", body)

    def test_delete_item_removes_record_and_updates_summary_counts(self) -> None:
        self._create_item(item_name="Kindle", category_key="tablet")
        self._create_item(item_name="iPhone 12", category_key="phone", price="100.00", purchase_date="2026-05-15")
        self.client.post(
            "/items/2/retirement",
            data={
                "action": "retire",
                "retired_on": "2026-05-18",
                "retired_reason": "升级换代",
                "resale_price": "",
                "retired_note": "",
            },
        )

        response = self.client.post("/items/1/delete", follow_redirects=True)
        body = response.get_data(as_text=True)

        self.assertIn("该资产记录已删除", body)
        self.assertNotIn("Kindle", body)
        self.assertIn("iPhone 12", body)
        self.assertIn(">1</strong>", body)
        self.assertIn("使用中", body)
        self.assertIn("已退役", body)

    def test_export_route_returns_current_json_payload(self) -> None:
        self._create_item()
        self.client.post(
            "/items/1/retirement",
            data={
                "action": "retire",
                "retired_on": "2026-05-21",
                "retired_reason": "升级换代",
                "resale_price": "200.00",
                "retired_note": "卖给朋友",
            },
        )

        response = self.client.get("/items/export")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        payload = json.loads(response.get_data(as_text=True))
        self.assertEqual(payload["items"][0]["category_key"], "tablet")
        self.assertEqual(payload["items"][0]["item_note"], "阅读器")
        self.assertEqual(payload["items"][0]["retired_reason"], "升级换代")
        self.assertEqual(payload["items"][0]["resale_price_cents"], 20000)

    def test_import_route_restores_current_json(self) -> None:
        payload = {
            "schema_version": 1,
            "items": [
                {
                    "id": 1,
                    "item_name": "Imported Kindle",
                    "category_key": "tablet",
                    "price_cents": 90000,
                    "purchase_date": "2026-05-18",
                    "item_note": "导入备注",
                    "created_at": "2026-05-21 19:00:00",
                    "retired_on": "2026-05-20",
                    "retired_reason": "升级换代",
                    "resale_price_cents": 30000,
                    "retired_note": "已卖出",
                }
            ],
        }

        response = self.client.post(
            "/items/import",
            data={"import_file": (io.BytesIO(json.dumps(payload).encode("utf-8")), "dayavg-export.json")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Imported Kindle", body)
        self.assertIn("导入备注", body)
        self.assertIn("实际成本 \u00a5600.00", body)
        self.assertIn("资产数据已从 JSON 导入", body)

    def test_invalid_import_does_not_overwrite_existing_data(self) -> None:
        self._create_item(item_name="Existing Asset", category_key="other", price="100.00", item_note="原始数据")

        response = self.client.post(
            "/items/import",
            data={"import_file": (io.BytesIO(b'{"bad": true}'), "broken.json")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Existing Asset", body)
        self.assertIn("schema_version", body)
        self.assertIn("原始数据", body)


if __name__ == "__main__":
    unittest.main()
