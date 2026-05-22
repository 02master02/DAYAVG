from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from dayavg.services.calculator import calculate_item_state
from dayavg.storage.repository import StoredItemRecord

EXPORT_SCHEMA_VERSION = 1


class ImportValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def build_export_payload(records: list[StoredItemRecord]) -> dict[str, Any]:
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "items": [
            {
                "id": record.id,
                "item_name": record.item_name,
                "price_cents": record.price_cents,
                "purchase_date": record.purchase_date,
                "created_at": record.created_at,
                "retired_on": record.retired_on,
                "retired_note": record.retired_note,
            }
            for record in records
        ],
    }


def parse_import_payload(raw_text: str, *, current_date: date) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ImportValidationError(f"导入文件不是有效的 JSON：{exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ImportValidationError("导入 JSON 的根节点必须是对象。")

    schema_version = payload.get("schema_version")
    if schema_version != EXPORT_SCHEMA_VERSION:
        raise ImportValidationError("导入 JSON 的 schema_version 不受支持。")

    items = payload.get("items")
    if not isinstance(items, list):
        raise ImportValidationError("导入 JSON 缺少有效的 items 数组。")

    normalized_items: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for index, item in enumerate(items, start=1):
        normalized_items.append(
            _normalize_import_item(item, index=index, current_date=current_date, seen_ids=seen_ids)
        )
    return normalized_items


def _normalize_import_item(
    item: Any,
    *,
    index: int,
    current_date: date,
    seen_ids: set[int],
) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ImportValidationError(f"第 {index} 条资产必须是对象。")

    item_id = _require_positive_int(item.get("id"), f"第 {index} 条资产的 id")
    if item_id in seen_ids:
        raise ImportValidationError(f"第 {index} 条资产的 id 与其它资产重复。")
    seen_ids.add(item_id)

    item_name = item.get("item_name")
    if not isinstance(item_name, str) or not item_name.strip():
        raise ImportValidationError(f"第 {index} 条资产缺少有效的 item_name。")
    item_name = item_name.strip()
    if len(item_name) > 120:
        raise ImportValidationError(f"第 {index} 条资产的 item_name 超过 120 个字符。")

    price_cents = _require_positive_int(item.get("price_cents"), f"第 {index} 条资产的 price_cents")
    purchase_date = _parse_iso_date(item.get("purchase_date"), f"第 {index} 条资产的 purchase_date")
    if purchase_date > current_date:
        raise ImportValidationError(f"第 {index} 条资产的 purchase_date 不能晚于今天。")

    created_at = _parse_timestamp(item.get("created_at"), f"第 {index} 条资产的 created_at")

    retired_on_raw = item.get("retired_on")
    retired_on: str | None = None
    reference_date = current_date
    if retired_on_raw is not None:
        retired_on_date = _parse_iso_date(retired_on_raw, f"第 {index} 条资产的 retired_on")
        if retired_on_date < purchase_date:
            raise ImportValidationError(f"第 {index} 条资产的 retired_on 不能早于 purchase_date。")
        if retired_on_date > current_date:
            raise ImportValidationError(f"第 {index} 条资产的 retired_on 不能晚于今天。")
        retired_on = retired_on_date.isoformat()
        reference_date = retired_on_date

    retired_note_raw = item.get("retired_note")
    if retired_note_raw is None:
        retired_note = None
    elif isinstance(retired_note_raw, str):
        retired_note = retired_note_raw.strip() or None
    else:
        raise ImportValidationError(f"第 {index} 条资产的 retired_note 必须是字符串或 null。")

    if retired_note is not None and len(retired_note) > 200:
        raise ImportValidationError(f"第 {index} 条资产的 retired_note 超过 200 个字符。")

    state = calculate_item_state(price_cents, purchase_date, reference_date)
    return {
        "id": item_id,
        "item_name": item_name,
        "price_cents": price_cents,
        "purchase_date": purchase_date.isoformat(),
        "held_days": state["held_days"],
        "daily_cost_cents": state["daily_cost_cents"],
        "created_at": created_at,
        "retired_on": retired_on,
        "retired_note": retired_note,
    }


def _require_positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ImportValidationError(f"{label} 必须是大于 0 的整数。")
    return value


def _parse_iso_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise ImportValidationError(f"{label} 必须是 YYYY-MM-DD 字符串。")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ImportValidationError(f"{label} 不是有效的日期。") from exc


def _parse_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ImportValidationError(f"{label} 必须是时间字符串。")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ImportValidationError(f"{label} 不是有效的时间格式。") from exc
    return parsed.replace(microsecond=0).isoformat(sep=" ")
