import re

__all__ = ["redact"]

PATTERNS = [
    # Claude Code system payloads (task-notification blocks, tool-use IDs, internal paths)
    (re.compile(r'<task-notification>.*?</task-notification>', re.DOTALL), '[REDACTED:cc-task]'),
    (re.compile(r'<(?:task-id|tool-use-id|output-file)>[^<]*</(?:task-id|tool-use-id|output-file)>'), '[REDACTED:cc-meta]'),
    (re.compile(r'\btoolu_[A-Za-z0-9]{20,}'), '[REDACTED:tool-use-id]'),
    (re.compile(r'/private/tmp/claude-\d+/[^\s]*'), '[REDACTED:cc-tmp]'),
    # API keys / cloud tokens
    (re.compile(r'(sk-|pk_)[a-zA-Z0-9_-]{20,}'),                          '[REDACTED:api-key]'),
    (re.compile(r'AKIA[0-9A-Z]{16}'),                                     '[REDACTED:aws]'),
    (re.compile(r'gh[pso]_[a-zA-Z0-9]{36,}'),                             '[REDACTED:gh]'),
    (re.compile(r'ey[JK][A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), '[REDACTED:jwt]'),
    # Webhooks
    (re.compile(r'https://hooks\.slack\.com/services/[A-Z0-9/]+'),        '[REDACTED:slack-webhook]'),
    (re.compile(r'https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+'), '[REDACTED:discord-webhook]'),
    # Auth headers / URL-embedded secrets
    (re.compile(r'Bearer [A-Za-z0-9_\-\.=:]+'),                           '[REDACTED:bearer]'),
    (re.compile(r'([?&](?:token|api_key|apikey|key|secret|password)=)[^&\s]+'), r'\1[REDACTED]'),
    # Home paths (username leak)
    (re.compile(r'/Users/[^/\s]+/'),                                      '/Users/[REDACTED]/'),
    (re.compile(r'/home/[^/\s]+/'),                                       '/home/[REDACTED]/'),
    # Contact info
    (re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),       '[REDACTED:email]'),
    (re.compile(r'01[0-9]-?[0-9]{3,4}-?[0-9]{4}'),                        '[REDACTED:phone]'),
    # Network / financial
    (re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),                    '[REDACTED:ipv4]'),
    (re.compile(r'\b[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b'), '[REDACTED:card]'),
]


def redact(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text
