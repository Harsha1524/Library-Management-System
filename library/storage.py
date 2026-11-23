"""Save / load a ``Library`` as JSON."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .service import Library


def save(library: Library, path: str | os.PathLike[str]) -> None:
    """Write atomically: a crash mid-save must not leave a half-written data file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(library.to_dict(), fh, indent=2, ensure_ascii=False)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def load(path: str | os.PathLike[str]) -> Library:
    """Load a library, or return an empty one if the file does not exist yet."""
    path = Path(path)
    if not path.exists():
        return Library()
    with path.open(encoding="utf-8") as fh:
        return Library.from_dict(json.load(fh))
