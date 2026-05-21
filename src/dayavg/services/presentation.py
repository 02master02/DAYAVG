from __future__ import annotations

from typing import Any, Mapping

from dayavg.services.calculator import average_cents, format_currency


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


def classify_item_visual(item_name: str) -> dict[str, str]:
    normalized = item_name.lower()
    rules = [
        (
            ("iphone", "phone", "手机", "meizu", "xiaomi", "huawei", "samsung", "vivo", "oppo", "redmi"),
            "phone",
            "手机",
        ),
        (
            ("macbook", "laptop", "notebook", "thinkpad", "surface", "电脑", "笔记本", "显示器", "monitor", "display", "screen", "主机"),
            "computer",
            "电脑",
        ),
        (("kindle", "ipad", "tablet", "平板", "阅读器"), "tablet", "平板"),
        (("watch", "band", "apple watch", "手表", "手环", "表带", "mi band"), "wearable", "手环手表"),
        (("car", "tesla", "byd", "audi", "bmw", "benz", "toyota", "honda", "车", "汽车", "摩托", "电动车"), "car", "车子"),
        (("shoes", "shoe", "sneaker", "boot", "鞋", "跑鞋", "拖鞋", "靴"), "shoes", "鞋子"),
        (("shirt", "coat", "jacket", "hoodie", "pants", "clothes", "衣服", "外套", "裤", "衬衫", "羽绒服", "裙"), "clothes", "衣服"),
    ]

    for keywords, icon_kind, label in rules:
        if any(keyword in normalized for keyword in keywords):
            return _build_visual(icon_kind, label)

    office_keywords = (
        "mouse", "keyboard", "printer", "scanner", "paper", "pen", "pencil", "office",
        "desk", "lamp", "router", "cable", "adapter", "dock", "speaker", "headset",
        "鼠标", "键盘", "打印机", "扫描仪", "纸", "笔", "文具", "办公", "工位", "台灯", "路由器", "数据线", "转接器", "扩展坞", "音箱", "耳机",
    )
    if any(keyword in normalized for keyword in office_keywords):
        return _build_visual("office", "办公用品")

    life_keywords = (
        "cup", "bottle", "kettle", "toothbrush", "soap", "shampoo", "blanket", "pillow",
        "bag", "backpack", "fan", "cleaner", "tissue", "生活", "日用", "杯", "水壶", "牙刷",
        "洗发水", "沐浴露", "纸巾", "枕头", "被子", "背包", "风扇", "清洁", "护肤", "毛巾",
    )
    if any(keyword in normalized for keyword in life_keywords):
        return _build_visual("life", "生活用品")

    return _build_visual("other", "其他")


def _build_visual(icon_kind: str, label: str) -> dict[str, str]:
    return {
        "icon_kind": icon_kind,
        "icon_filename": f"{icon_kind}.png",
        "theme_class": f"theme-{icon_kind}",
        "category_label": label,
    }
