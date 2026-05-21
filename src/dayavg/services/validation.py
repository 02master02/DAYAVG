from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Mapping

from dayavg.services.calculator import calculate_item_state, decimal_to_cents


class FormValidationError(Exception):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Invalid form input")
        self.errors = errors


@dataclass(frozen=True)
class ParsedItemForm:
    item_name: str
    price: Decimal
    price_cents: int
    purchase_date: date
    held_days: int
    daily_cost_cents: int


@dataclass(frozen=True)
class ParsedRetirementForm:
    retired_on: date
    retired_note: str
    held_days: int
    daily_cost_cents: int


def parse_item_form(
    form_data: Mapping[str, str],
    *,
    current_date: date,
    max_purchase_date: date | None = None,
    max_purchase_date_label: str = "今天",
) -> ParsedItemForm:
    errors: dict[str, str] = {}

    item_name = form_data.get("item_name", "").strip()
    if not item_name:
        errors["item_name"] = "请输入物品名称。"

    price_text = form_data.get("price", "").strip()
    price_value: Decimal | None = None
    if not price_text:
        errors["price"] = "请输入购买价格。"
    else:
        try:
            price_value = Decimal(price_text)
        except InvalidOperation:
            errors["price"] = "购买价格必须是有效数字。"
        else:
            if price_value <= 0:
                errors["price"] = "购买价格必须大于 0。"
            elif price_value.quantize(Decimal("0.01")) != price_value:
                errors["price"] = "购买价格最多保留两位小数。"

    purchase_date_text = form_data.get("purchase_date", "").strip()
    purchase_date_value: date | None = None
    if not purchase_date_text:
        errors["purchase_date"] = "请输入购买日期。"
    else:
        try:
            purchase_date_value = date.fromisoformat(purchase_date_text)
        except ValueError:
            errors["purchase_date"] = "购买日期格式必须是 YYYY-MM-DD。"
        else:
            effective_max_date = max_purchase_date or current_date
            if purchase_date_value > effective_max_date:
                errors["purchase_date"] = f"购买日期不能晚于{max_purchase_date_label}。"

    if errors:
        raise FormValidationError(errors)

    assert price_value is not None
    assert purchase_date_value is not None

    price_cents = decimal_to_cents(price_value)
    state = calculate_item_state(price_cents, purchase_date_value, max_purchase_date or current_date)

    return ParsedItemForm(
        item_name=item_name,
        price=price_value,
        price_cents=price_cents,
        purchase_date=purchase_date_value,
        held_days=state["held_days"],
        daily_cost_cents=state["daily_cost_cents"],
    )


def parse_retirement_form(
    form_data: Mapping[str, str],
    *,
    purchase_date: date,
    current_date: date,
    price_cents: int,
) -> ParsedRetirementForm:
    errors: dict[str, str] = {}

    retired_on_text = form_data.get("retired_on", "").strip()
    retired_on_value: date | None = None
    if not retired_on_text:
        errors["retired_on"] = "请输入退役日期。"
    else:
        try:
            retired_on_value = date.fromisoformat(retired_on_text)
        except ValueError:
            errors["retired_on"] = "退役日期格式必须是 YYYY-MM-DD。"
        else:
            if retired_on_value < purchase_date:
                errors["retired_on"] = "退役日期不能早于购买日期。"
            elif retired_on_value > current_date:
                errors["retired_on"] = "退役日期不能晚于今天。"

    retired_note = form_data.get("retired_note", "").strip()
    if len(retired_note) > 200:
        errors["retired_note"] = "退役备注最多 200 个字符。"

    if errors:
        raise FormValidationError(errors)

    assert retired_on_value is not None

    state = calculate_item_state(price_cents, purchase_date, retired_on_value)
    return ParsedRetirementForm(
        retired_on=retired_on_value,
        retired_note=retired_note,
        held_days=state["held_days"],
        daily_cost_cents=state["daily_cost_cents"],
    )
