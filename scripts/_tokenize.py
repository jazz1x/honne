#!/usr/bin/env python3
"""Re-export shim for backward compatibility. Delegates to honne_py.tokenize_text."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from honne_py.tokenize_text import tokenize

if __name__ == "__main__":
    text = sys.stdin.read()
    for token in tokenize(text):
        print(token)
