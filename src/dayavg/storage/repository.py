from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StoredItemRecord:
    id: int
    item_name: str
    price_cents: int
    purchase_date: str
    held_days: int
    daily_cost_cents: int
    created_at: str
    retired_on: str | None
    retired_note: str | None


class DayAvgRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    price_cents INTEGER NOT NULL,
                    purchase_date TEXT NOT NULL,
                    held_days INTEGER NOT NULL,
                    daily_cost_cents INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(items)").fetchall()
            }
            if "retired_on" not in columns:
                connection.execute("ALTER TABLE items ADD COLUMN retired_on TEXT")
            if "retired_note" not in columns:
                connection.execute("ALTER TABLE items ADD COLUMN retired_note TEXT")
            connection.commit()

    def add_item(
        self,
        *,
        item_name: str,
        price_cents: int,
        purchase_date: str,
        held_days: int,
        daily_cost_cents: int,
    ) -> StoredItemRecord:
        created_at = datetime.now().replace(microsecond=0).isoformat(sep=" ")
        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                """
                INSERT INTO items (
                    item_name,
                    price_cents,
                    purchase_date,
                    held_days,
                    daily_cost_cents,
                    created_at,
                    retired_on,
                    retired_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (item_name, price_cents, purchase_date, held_days, daily_cost_cents, created_at, None, None),
            )
            connection.commit()
            item_id = int(cursor.lastrowid)
        return self.get_item(item_id)  # type: ignore[return-value]

    def update_item(
        self,
        item_id: int,
        *,
        price_cents: int,
        purchase_date: str,
        held_days: int,
        daily_cost_cents: int,
    ) -> StoredItemRecord | None:
        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                """
                UPDATE items
                SET
                    price_cents = ?,
                    purchase_date = ?,
                    held_days = ?,
                    daily_cost_cents = ?
                WHERE id = ?
                """,
                (price_cents, purchase_date, held_days, daily_cost_cents, item_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_item(item_id)

    def update_retirement(
        self,
        item_id: int,
        *,
        retired_on: str | None,
        retired_note: str | None,
        held_days: int,
        daily_cost_cents: int,
    ) -> StoredItemRecord | None:
        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                """
                UPDATE items
                SET
                    retired_on = ?,
                    retired_note = ?,
                    held_days = ?,
                    daily_cost_cents = ?
                WHERE id = ?
                """,
                (retired_on, retired_note, held_days, daily_cost_cents, item_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_item(item_id)

    def get_item(self, item_id: int | None) -> StoredItemRecord | None:
        if item_id is None:
            return None
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT id, item_name, price_cents, purchase_date, held_days, daily_cost_cents, created_at, retired_on, retired_note
                FROM items
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()
        return self._row_to_record(row) if row else None

    def list_items(self) -> list[StoredItemRecord]:
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, item_name, price_cents, purchase_date, held_days, daily_cost_cents, created_at, retired_on, retired_note
                FROM items
                ORDER BY datetime(created_at) DESC, id DESC
                """
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def replace_items(self, items: list[dict[str, Any]]) -> None:
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute("DELETE FROM items")
            connection.execute("DELETE FROM sqlite_sequence WHERE name = 'items'")
            if items:
                connection.executemany(
                    """
                    INSERT INTO items (
                        id,
                        item_name,
                        price_cents,
                        purchase_date,
                        held_days,
                        daily_cost_cents,
                        created_at,
                        retired_on,
                        retired_note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item["id"],
                            item["item_name"],
                            item["price_cents"],
                            item["purchase_date"],
                            item["held_days"],
                            item["daily_cost_cents"],
                            item["created_at"],
                            item["retired_on"],
                            item["retired_note"],
                        )
                        for item in items
                    ],
                )
                max_item_id = max(int(item["id"]) for item in items)
                connection.execute("DELETE FROM sqlite_sequence WHERE name = 'items'")
                connection.execute(
                    "INSERT INTO sqlite_sequence(name, seq) VALUES('items', ?)",
                    (max_item_id,),
                )
            connection.commit()

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> StoredItemRecord:
        return StoredItemRecord(
            id=int(row["id"]),
            item_name=str(row["item_name"]),
            price_cents=int(row["price_cents"]),
            purchase_date=str(row["purchase_date"]),
            held_days=int(row["held_days"]),
            daily_cost_cents=int(row["daily_cost_cents"]),
            created_at=str(row["created_at"]),
            retired_on=str(row["retired_on"]) if row["retired_on"] is not None else None,
            retired_note=str(row["retired_note"]) if row["retired_note"] is not None else None,
        )
