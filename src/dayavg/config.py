from __future__ import annotations

import os
from pathlib import Path


def build_default_config(repo_root: Path) -> dict[str, object]:
    database_path = repo_root / "outputs" / "dayavg.db"
    return {
        "SECRET_KEY": os.environ.get("DAYAVG_SECRET_KEY", "dayavg-local-dev"),
        "DATABASE_PATH": os.environ.get("DAYAVG_DB_PATH", str(database_path)),
        "HOST": os.environ.get("DAYAVG_HOST", "0.0.0.0"),
        "PORT": int(os.environ.get("DAYAVG_PORT", "5000")),
        "DEBUG": False,
        "TODAY_OVERRIDE": None,
    }
