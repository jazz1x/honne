import re
import sys

TOKEN = re.compile(r'[^\W_]+', re.UNICODE)


def tokenize(text: str):
    """Yield lowercased tokens from text."""
    for match in TOKEN.finditer(text):
        yield match.group().lower()


if __name__ == "__main__":
    text = sys.stdin.read()
    for token in tokenize(text):
        print(token)
