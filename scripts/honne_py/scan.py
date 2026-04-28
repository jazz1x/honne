import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Union, Optional

from .io import atomic_write, sha256_file
from .redact import redact

_META_BLACKLIST = (
    "Base directory for this skill:",
    "<command-message>",
    "<command-name>",
    "This session is being continued",
    "<local-command-stdout>",
    "<local-command-stderr>",
    "<local-command-caveat>",
    "<system-reminder>",
    "CRITICAL: Respond with TEXT ONLY",
)

_ASSISTANT_LEAK_PREFIXES = ("## 🎉", "✅", "🎉", "# Milestone")


def _is_meta_preamble(text: str) -> bool:
    stripped = text.lstrip()
    return any(stripped.startswith(marker) for marker in _META_BLACKLIST)


def _is_assistant_leak(text: str) -> bool:
    stripped = text.lstrip()
    if any(stripped.startswith(p) for p in _ASSISTANT_LEAK_PREFIXES):
        return True
    if text.count("✅") >= 3:
        return True
    return False


def run_scan(
    scope: Literal["global", "repo"],
    since: str,
    cache: Union[Path, str],
    index_ref: Optional[Union[Path, str]] = None,
    redact_secrets: bool = True,
    base_dir: Optional[Union[Path, str]] = None,
    run_id: Optional[str] = None,
) -> int:
    """Scan transcripts from scope, write to cache JSONL.

    Returns: 0 success, 2 empty result, 1 error.
    Emits progress to stderr: [scan] N/M every 100 files or 5 seconds.
    """
    cache = Path(cache)
    if run_id is None:
        run_id = uuid.uuid4().hex
    index_ref = Path(index_ref) if index_ref else None

    # Scope → path resolution
    if scope == "global":
        search_dir = Path.home() / ".claude" / "projects"
    elif scope == "repo":
        # Use $PWD env var (bash sets it without resolving symlinks)
        # so slug matches what the shell-based callers expect on macOS
        cwd_str = os.environ.get("PWD", os.getcwd())
        slug = cwd_str.replace("/", "-").lstrip("-")
        search_dir = Path.home() / ".claude" / "projects" / slug
        if not search_dir.exists() or not any(search_dir.iterdir()):
            sys.stderr.write(f"[scan] repo scope: no transcripts at {search_dir}\n")
            return 2
    else:
        sys.stderr.write(f"[scan] invalid scope: {scope}\n")
        return 1

    # Load known SHAs (idempotent skip)
    known_shas = set()
    if index_ref and index_ref.exists():
        try:
            with open(index_ref) as f:
                data = json.load(f)
                for session in data.get("sessions", []):
                    sha = session.get("sha256")
                    if sha:
                        known_shas.add(sha)
        except Exception:
            pass

    # Collect .jsonl files
    jsonl_files = sorted(search_dir.glob("**/*.jsonl")) if search_dir.exists() else []

    if not jsonl_files:
        sys.stderr.write(f"[scan] no transcripts found\n")
        return 2

    sessions = []
    found = 0
    last_progress = time.monotonic()
    start_time = time.monotonic()

    for file_idx, jsonl_path in enumerate(jsonl_files):
        now = time.monotonic()
        # Progress: every 100 files or 5 sec
        if file_idx % 100 == 0 or (now - last_progress) >= 5.0:
            sys.stderr.write(f"[scan] {file_idx}/{len(jsonl_files)}\n")
            sys.stderr.flush()
            last_progress = now

        # SHA256 skip
        try:
            sha = sha256_file(jsonl_path)
            if sha in known_shas:
                continue
        except Exception:
            continue

        # Since filter
        file_mtime = datetime.fromtimestamp(jsonl_path.stat().st_mtime).strftime("%Y-%m-%d")
        if file_mtime < since[:10]:
            continue

        # Parse session
        try:
            session_dict = _parse_jsonl(jsonl_path, redact_secrets)
            if not session_dict:
                continue
        except Exception:
            continue

        session_dict["sha256"] = sha
        sessions.append(session_dict)
        found += 1

    # Final progress
    sys.stderr.write(f"[scan] {len(jsonl_files)}/{len(jsonl_files)}\n")
    sys.stderr.flush()

    if not sessions:
        sys.stderr.write(f"[scan] no sessions matched\n")
        return 2

    # Write cache atomically
    result = {
        "run_id": run_id,
        "scope": scope,
        "scanned_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sessions": sessions,
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(cache, json.dumps(result) + "\n")
    sys.stderr.write(f"[scan] scanned {found} sessions → {cache}\n")
    # stdout summary for bats $output capture
    print(f"scanned {found} sessions → {cache}")

    return 0


def _parse_jsonl(jsonl_path: Path, redact_secrets: bool = True) -> Optional[dict]:
    """Parse single JSONL file. Returns session dict or None."""
    messages = []

    with open(jsonl_path) as f:
        for line_idx, line in enumerate(f):
            if not line.strip():
                continue

            try:
                obj = json.loads(line)
            except Exception:
                continue

            # Extract message
            msg_obj = obj.get("message", {})
            role = msg_obj.get("role")
            if not role:
                continue

            # Extract text from content (string or array)
            content = msg_obj.get("content", "")
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        # Claude Code format: {"type": "text", "text": "..."}
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        # Fallback: {"text": "..."} without type
                        elif "text" in item and "type" not in item:
                            text_parts.append(item.get("text", ""))
                text = "\n".join(text_parts)
            else:
                text = ""

            if not text or not text.strip():
                continue

            # Skip meta/preamble injections and assistant-leak messages
            if role == "user" and (_is_meta_preamble(text) or _is_assistant_leak(text)):
                continue

            # Redact
            if redact_secrets:
                text = redact(text)

            messages.append({
                "role": role,
                "text": text,
                "ts": obj.get("timestamp", ""),
            })

    if not messages:
        return None

    # Extract metadata from first line
    with open(jsonl_path) as f:
        first_line = f.readline()
        try:
            first_obj = json.loads(first_line)
            session_id = first_obj.get("sessionId", "")
            cwd = first_obj.get("cwd", "")
            started_at = first_obj.get("timestamp", "")
        except Exception:
            return None

    if not session_id:
        return None

    return {
        "session_id": session_id,
        "project_path": cwd,
        "started_at": started_at,
        "messages": messages,
    }


