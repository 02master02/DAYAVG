from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from flask import Flask, flash, redirect, render_template, request, url_for

from dayavg.config import build_default_config
from dayavg.services.calculator import calculate_item_state, format_currency, format_timestamp
from dayavg.services.presentation import classify_item_visual, summarize_history
from dayavg.services.validation import FormValidationError, parse_item_form, parse_retirement_form
from dayavg.storage.repository import DayAvgRepository, StoredItemRecord


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    repo_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(repo_root / "templates"),
        static_folder=str(repo_root / "static"),
    )
    app.config.from_mapping(build_default_config(repo_root))
    if test_config:
        app.config.update(test_config)

    repository = DayAvgRepository(Path(app.config["DATABASE_PATH"]))
    repository.initialize()
    app.config["REPOSITORY"] = repository

    @app.get("/")
    def index() -> str:
        today = _current_date(app)
        created_id = request.args.get("created_id", type=int)
        updated_id = request.args.get("updated_id", type=int)
        editing_id = request.args.get("editing_id", type=int)
        retiring_id = request.args.get("retiring_id", type=int)
        focus_id = created_id or updated_id
        latest_record = repository.get_item(focus_id) if focus_id else None
        return render_template(
            "index.html",
            **_build_page_context(
                repository,
                latest_record=latest_record,
                editing_id=editing_id,
                retiring_id=retiring_id,
                today=today,
            ),
        )

    @app.post("/items")
    def create_item() -> str:
        today = _current_date(app)
        form_values = {
            "item_name": request.form.get("item_name", "").strip(),
            "price": request.form.get("price", "").strip(),
            "purchase_date": request.form.get("purchase_date", "").strip(),
        }

        try:
            parsed = parse_item_form(form_values, current_date=today)
        except FormValidationError as exc:
            return render_template(
                "index.html",
                **_build_page_context(
                    repository,
                    create_errors=exc.errors,
                    create_form_values=form_values,
                    today=today,
                ),
            )

        created_record = repository.add_item(
            item_name=parsed.item_name,
            price_cents=parsed.price_cents,
            purchase_date=parsed.purchase_date.isoformat(),
            held_days=parsed.held_days,
            daily_cost_cents=parsed.daily_cost_cents,
        )
        flash("记录已保存，并已完成日均持有成本计算。", "success")
        return redirect(url_for("index", created_id=created_record.id))

    @app.post("/items/<int:item_id>/edit")
    def edit_item(item_id: int) -> str:
        today = _current_date(app)
        existing_record = repository.get_item(item_id)
        if existing_record is None:
            flash("未找到要修改的物品记录。", "error")
            return redirect(url_for("index"))

        edit_form_values = {
            "price": request.form.get("price", "").strip(),
            "purchase_date": request.form.get("purchase_date", "").strip(),
        }
        candidate_form = {
            "item_name": existing_record.item_name,
            "price": edit_form_values["price"],
            "purchase_date": edit_form_values["purchase_date"],
        }

        max_purchase_date = date.fromisoformat(existing_record.retired_on) if existing_record.retired_on else today
        max_date_label = "退役日期" if existing_record.retired_on else "今天"

        try:
            parsed = parse_item_form(
                candidate_form,
                current_date=today,
                max_purchase_date=max_purchase_date,
                max_purchase_date_label=max_date_label,
            )
        except FormValidationError as exc:
            edit_errors = {
                key: value for key, value in exc.errors.items() if key in {"price", "purchase_date"}
            }
            return render_template(
                "index.html",
                **_build_page_context(
                    repository,
                    editing_id=item_id,
                    edit_errors=edit_errors,
                    edit_form_values=edit_form_values,
                    today=today,
                ),
            )

        updated_record = repository.update_item(
            item_id,
            price_cents=parsed.price_cents,
            purchase_date=parsed.purchase_date.isoformat(),
            held_days=parsed.held_days,
            daily_cost_cents=parsed.daily_cost_cents,
        )
        if updated_record is None:
            flash("修改失败，记录不存在。", "error")
            return redirect(url_for("index"))

        flash("记录已更新，价格和购买日期已重新计算。", "success")
        return redirect(url_for("index", updated_id=updated_record.id))

    @app.post("/items/<int:item_id>/retirement")
    def update_retirement(item_id: int) -> str:
        today = _current_date(app)
        existing_record = repository.get_item(item_id)
        if existing_record is None:
            flash("未找到要更新状态的物品记录。", "error")
            return redirect(url_for("index"))

        action = request.form.get("action", "").strip()
        purchase_date = date.fromisoformat(existing_record.purchase_date)

        if action == "retire":
            retire_form_values = {
                "retired_on": request.form.get("retired_on", "").strip(),
                "retired_note": request.form.get("retired_note", "").strip(),
            }
            try:
                parsed = parse_retirement_form(
                    retire_form_values,
                    purchase_date=purchase_date,
                    current_date=today,
                    price_cents=existing_record.price_cents,
                )
            except FormValidationError as exc:
                return render_template(
                    "index.html",
                    **_build_page_context(
                        repository,
                        retiring_id=item_id,
                        retire_errors=exc.errors,
                        retire_form_values=retire_form_values,
                        today=today,
                    ),
                )

            updated_record = repository.update_retirement(
                item_id,
                retired_on=parsed.retired_on.isoformat(),
                retired_note=parsed.retired_note or None,
                held_days=parsed.held_days,
                daily_cost_cents=parsed.daily_cost_cents,
            )
            if updated_record is not None:
                flash("该物品已保存退役设置，后续将冻结在退役日期。", "success")
        elif action == "restore":
            state = calculate_item_state(existing_record.price_cents, purchase_date, today)
            updated_record = repository.update_retirement(
                item_id,
                retired_on=None,
                retired_note=None,
                held_days=state["held_days"],
                daily_cost_cents=state["daily_cost_cents"],
            )
            if updated_record is not None:
                flash("该物品已恢复使用，将继续随时间更新。", "success")
        else:
            flash("无效的退役操作。", "error")

        return redirect(url_for("index", updated_id=item_id))

    return app


def _current_date(app: Flask) -> date:
    override = app.config.get("TODAY_OVERRIDE")
    if isinstance(override, date):
        return override
    if isinstance(override, str) and override:
        return date.fromisoformat(override)
    return date.today()


def _build_page_context(
    repository: DayAvgRepository,
    *,
    today: date,
    latest_record: StoredItemRecord | None = None,
    create_errors: dict[str, str] | None = None,
    create_form_values: dict[str, str] | None = None,
    editing_id: int | None = None,
    edit_errors: dict[str, str] | None = None,
    edit_form_values: dict[str, str] | None = None,
    retiring_id: int | None = None,
    retire_errors: dict[str, str] | None = None,
    retire_form_values: dict[str, str] | None = None,
) -> dict[str, Any]:
    history_records = repository.list_items()
    history_views = [_build_record_view(item, today=today) for item in history_records]
    editing_record = repository.get_item(editing_id) if editing_id else None
    retiring_record = repository.get_item(retiring_id) if retiring_id else None
    normalized_edit_values = edit_form_values or (
        {
            "price": _price_to_plain_string(editing_record.price_cents),
            "purchase_date": editing_record.purchase_date,
        }
        if editing_record
        else {"price": "", "purchase_date": ""}
    )
    normalized_retire_values = retire_form_values or (
        {
            "retired_on": retiring_record.retired_on or today.isoformat(),
            "retired_note": retiring_record.retired_note or "",
        }
        if retiring_record
        else {"retired_on": today.isoformat(), "retired_note": ""}
    )
    return {
        "errors": create_errors or {},
        "form_values": create_form_values or _empty_form_values(),
        "latest_record": _build_record_view(latest_record, today=today) if latest_record else None,
        "history": history_views,
        "summary": summarize_history(history_views),
        "today": today.isoformat(),
        "editing_id": editing_id,
        "edit_errors": edit_errors or {},
        "edit_form_values": normalized_edit_values,
        "retiring_id": retiring_id,
        "retire_errors": retire_errors or {},
        "retire_form_values": normalized_retire_values,
    }


def _empty_form_values() -> dict[str, str]:
    return {"item_name": "", "price": "", "purchase_date": ""}


def _price_to_plain_string(price_cents: int) -> str:
    return f"{price_cents / 100:.2f}"


def _build_record_view(record: StoredItemRecord, *, today: date) -> dict[str, Any]:
    visuals = classify_item_visual(record.item_name)
    reference_date = date.fromisoformat(record.retired_on) if record.retired_on else today
    purchase_date = date.fromisoformat(record.purchase_date)
    state = calculate_item_state(record.price_cents, purchase_date, reference_date)
    is_retired = record.retired_on is not None
    note_suffix = f" · {record.retired_note}" if record.retired_note else ""
    return {
        "id": record.id,
        "item_name": record.item_name,
        "price_cents": record.price_cents,
        "price_display": format_currency(record.price_cents),
        "purchase_date": record.purchase_date,
        "held_days": state["held_days"],
        "daily_cost_cents": state["daily_cost_cents"],
        "daily_cost_display": format_currency(state["daily_cost_cents"]),
        "created_at_display": format_timestamp(record.created_at),
        "retired_on": record.retired_on,
        "retired_note": record.retired_note,
        "is_retired": is_retired,
        "status_label": "已退役" if is_retired else "使用中",
        "status_note": f"冻结于 {record.retired_on}{note_suffix}" if is_retired else "按今天实时更新",
        **visuals,
    }


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
