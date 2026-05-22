from __future__ import annotations

from typing import Any, Mapping

from dayavg.services.calculator import average_cents, format_currency

CATEGORY_DEFINITIONS = (
    {"key": "phone", "label": "手机", "icon_kind": "phone"},
    {"key": "computer", "label": "电脑", "icon_kind": "computer"},
    {"key": "tablet", "label": "平板", "icon_kind": "tablet"},
    {"key": "wearable", "label": "手环手表", "icon_kind": "wearable"},
    {"key": "car", "label": "车子", "icon_kind": "car"},
    {"key": "shoes", "label": "鞋子", "icon_kind": "shoes"},
    {"key": "clothes", "label": "衣服", "icon_kind": "clothes"},
    {"key": "office", "label": "办公用品", "icon_kind": "office"},
    {"key": "life", "label": "生活用品", "icon_kind": "life"},
    {"key": "other", "label": "其他", "icon_kind": "other"},
)
DEFAULT_CATEGORY_KEY = "other"
_CATEGORY_BY_KEY = {item["key"]: item for item in CATEGORY_DEFINITIONS}


def summarize_history(item_views: list[Mapping[str, Any]]) -> dict[str, Any]:
    prices = [int(item["price_cents"]) for item in item_views]
    daily_costs = [int(item["daily_cost_cents"]) for item in item_views]
    active_count = sum(1 for item in item_views if not item["is_retired"])
    retired_count = sum(1 for item in item_views if item["is_retired"])

    return {
        "item_count": len(item_views),
        "active_count": active_count,
        "retired_count": retired_count,
        "total_price_display": format_currency(sum(prices)),
        "total_daily_cost_display": format_currency(sum(daily_costs)),
        "average_price_display": format_currency(average_cents(prices)),
        "highest_daily_cost_display": format_currency(max(daily_costs) if daily_costs else 0),
        "lowest_daily_cost_display": format_currency(min(daily_costs) if daily_costs else 0),
    }


def get_category_options() -> list[dict[str, str]]:
    return [{"key": str(item["key"]), "label": str(item["label"])} for item in CATEGORY_DEFINITIONS]


def is_valid_category_key(category_key: str | None) -> bool:
    return category_key in _CATEGORY_BY_KEY


def normalize_category_key(category_key: str | None, item_name: str) -> str:
    if is_valid_category_key(category_key):
        return str(category_key)
    return infer_category_key(item_name)


def classify_item_visual(item_name: str, category_key: str | None = None) -> dict[str, str]:
    resolved_key = normalize_category_key(category_key, item_name)
    category = _CATEGORY_BY_KEY[resolved_key]
    return _build_visual(str(category["icon_kind"]), str(category["label"]), resolved_key)


def infer_category_key(item_name: str) -> str:
    normalized = item_name.lower()
    rules = [
        (
            ("iphone", "phone", "手机", "meizu", "xiaomi", "huawei", "samsung", "vivo", "oppo", "redmi"),
            "phone",
        ),
        (
            ("macbook", "laptop", "notebook", "thinkpad", "surface", "电脑", "笔记本", "显示器", "monitor", "display", "screen", "主机"),
            "computer",
        ),
        (("kindle", "ipad", "tablet", "平板", "阅读器"), "tablet"),
        (("watch", "band", "apple watch", "手表", "手环", "表带", "mi band"), "wearable"),
        (("car", "tesla", "byd", "audi", "bmw", "benz", "toyota", "honda", "车", "汽车", "摩托", "电动车"), "car"),
        (("shoes", "shoe", "sneaker", "boot", "鞋", "跑鞋", "拖鞋", "靴"), "shoes"),
        (("shirt", "coat", "jacket", "hoodie", "pants", "clothes", "衣服", "外套", "裤", "衬衫", "羽绒服", "裙"), "clothes"),
    ]

    for keywords, category_key in rules:
        if any(keyword in normalized for keyword in keywords):
            return category_key

    office_keywords = (
        "mouse", "keyboard", "printer", "scanner", "paper", "pen", "pencil", "office",
        "desk", "lamp", "router", "cable", "adapter", "dock", "speaker", "headset",
        "鼠标", "键盘", "打印机", "扫描仪", "纸", "笔", "文具", "办公", "工位", "台灯", "路由器", "数据线", "转接器", "扩展坞", "音箱", "耳机",
    )
    if any(keyword in normalized for keyword in office_keywords):
        return "office"

    life_keywords = (
        "cup", "bottle", "kettle", "toothbrush", "soap", "shampoo", "blanket", "pillow",
        "bag", "backpack", "fan", "cleaner", "tissue", "生活", "日用", "杯", "水壶", "牙刷",
        "洗发水", "沐浴露", "纸巾", "枕头", "被子", "背包", "风扇", "清洁", "护肤", "毛巾",
    )
    if any(keyword in normalized for keyword in life_keywords):
        return "life"

    return DEFAULT_CATEGORY_KEY


def _build_visual(icon_kind: str, label: str, category_key: str) -> dict[str, str]:
    return {
        "category_key": category_key,
        "icon_kind": icon_kind,
        "icon_filename": f"{icon_kind}.png",
        "theme_class": f"theme-{icon_kind}",
        "category_label": label,
    }
