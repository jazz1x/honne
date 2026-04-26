from typing import Union
import hashlib
import json
import tempfile
from pathlib import Path


def atomic_write(path: Union[Path, str], data: Union[bytes, str]) -> None:
    """Write to a temporary file, then atomically rename to target."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, str):
        data = data.encode("utf-8")

    with tempfile.NamedTemporaryFile(
        dir=path.parent, delete=False, suffix=".tmp"
    ) as f:
        temp_path = Path(f.name)
        f.write(data)

    temp_path.replace(path)


def sha256_file(path: Union[Path, str]) -> str:
    """Compute SHA256 hash of a file."""
    path = Path(path)
    hasher = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()


def load_cache(path: Union[Path, str]) -> Union[dict, list]:
    """Load JSON cache file. Return {} or [] if not found."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)
