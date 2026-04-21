#!/usr/bin/env python3
"""Tokenize Unicode word-like sequences from stdin, one lowercased token per line.

Matches letters + digits across scripts (Hangul, Kana, Kanji, Latin, Cyrillic, ...)
via \\w minus underscore. Used as the Python primary backend for honne lexicon
extraction. Called by extract-lexicon.sh when python3 is available.
"""
import re
import sys

# [^\W_] = \w without underscore = letters + digits, Unicode-aware by default (Python 3)
TOKEN = re.compile(r'[^\W_]+', re.UNICODE)

text = sys.stdin.read()
for match in TOKEN.finditer(text):
    print(match.group().lower())
