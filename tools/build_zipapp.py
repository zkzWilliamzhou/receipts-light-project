"""Build a single-file, dependency-free receipts.pyz using stdlib zipapp."""
from __future__ import annotations

import shutil
import stat
import sys
import tempfile
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "receipts.pyz"
ENTRY = "from receipts.cli import main\nraise SystemExit(main())\n"


def build() -> int:
    with tempfile.TemporaryDirectory() as td:
        stage = Path(td)
        shutil.copytree(ROOT / "receipts", stage / "receipts",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (stage / "__main__.py").write_text(ENTRY, encoding="utf-8")
        if TARGET.exists():
            TARGET.unlink()
        zipapp.create_archive(stage, target=TARGET,
                              interpreter="/usr/bin/env python3", compressed=True)
    TARGET.chmod(TARGET.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"built {TARGET.name}: {TARGET.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
