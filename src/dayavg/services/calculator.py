from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean
from typing import Iterable

MONEY_QUANTUM = Decimal("0.01")


def calculate_held_days(purchase_date: date, current_date: date) -> int:
    return max(1, (current_date - purchase_date).days + 1)


def cents_to_display_amount(cents: int) -> Decimal:
    return (Decimal(cents) / Decimal("100")).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def decimal_to_cents(amount: Decimal) -> int:
    quantized = amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    return int((quantized * 100).to_integral_value(rounding=ROUND_HALF_UP))


def calculate_daily_cost_cents(price_cents: int, held_days: int) -> int:
    daily_amount = (Decimal(price_cents) / Decimal("100")) / Decimal(held_days)
    return decimal_to_cents(daily_amount)


def calculate_actual_cost_cents(price_cents: int, resale_price_cents: int = 0) -> int:
    return max(0, price_cents - resale_price_cents)


def calculate_item_state(
    price_cents: int,
    purchase_date: date,
    current_date: date,
    *,
    resale_price_cents: int = 0,
) -> dict[str, int]:
    held_days = calculate_held_days(purchase_date, current_date)
    actual_cost_cents = calculate_actual_cost_cents(price_cents, resale_price_cents)
    return {
        "held_days": held_days,
        "actual_cost_cents": actual_cost_cents,
        "daily_cost_cents": calculate_daily_cost_cents(actual_cost_cents, held_days),
    }


def average_cents(values: Iterable[int]) -> int:
    items = list(values)
    if not items:
        return 0
    return int(round(mean(items)))


def format_currency(cents: int) -> str:
    amount = cents_to_display_amount(cents)
    return f"\u00a5{amount:,.2f}"


def format_timestamp(timestamp: str) -> str:
    parsed = datetime.fromisoformat(timestamp)
    return parsed.strftime("%Y-%m-%d %H:%M:%S")
