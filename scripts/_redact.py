#!/usr/bin/env python3
"""Re-export shim for backward compatibility. Delegates to honne_py.redact."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from honne_py.redact import *

if __name__ == "__main__":
    sys.stdout.write(redact(sys.stdin.read()))
