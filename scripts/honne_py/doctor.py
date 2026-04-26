import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    if not shutil.which("python3"):
        sys.stderr.write("python3 not found\n")
        return 71
    try:
        import honne_py  # noqa
    except ImportError:
        sys.stderr.write("honne_py module not importable\n")
        return 71
    honne_dir = Path(".honne")
    try:
        honne_dir.mkdir(exist_ok=True)
    except OSError:
        sys.stderr.write(".honne/ directory creation failed\n")
        return 73
    if not os.access(honne_dir, os.W_OK):
        sys.stderr.write(".honne/ not writable\n")
        return 73
    return 0
