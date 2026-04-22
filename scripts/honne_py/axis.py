from pathlib import Path
from typing import Optional
import json
import re
import sys
from . import extract, io as honne_io

AXES = ("lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern")
LOCALES = ("ko", "en", "jp")

_EXTRACTORS = {
    "lexicon":     extract.extract_lexicon,
    "reaction":    extract.extract_reaction,
    "workflow":    extract.extract_workflow,
    "obsession":   extract.extract_obsession,
    "ritual":      extract.extract_ritual,
    "antipattern": extract.extract_antipattern,
}


def _top_k(items: list, k: int = 3) -> list:
    """Deterministic top-k:
       1) frequency (or support_count) desc
       2) ts asc
       3) session_id asc (final tiebreak)
       Dedup by normalized text; keep first occurrence.
       Returns 0..k items if fewer candidates exist.
    """
    seen = set()
    dedup = []
    for it in items:
        t = (it.get("text") or it.get("quote") or "").strip()
        if not t or t in seen:
            continue
        seen.add(t)
        dedup.append(it)
    dedup.sort(key=lambda x: (
        -(x.get("frequency") or x.get("support_count") or 0),
        x.get("ts") or "",
        x.get("session_id") or "",
    ))
    return dedup[:k]


def _load_template(locale: str, axis: str) -> dict:
    """Parse templates/axes.<locale>.md.

    Invariants:
      1) Section identified by `## <axis_key>` exact match
      2) Each line `^- <key>: <value>$`
      3) Required keys: {label, hitl_question, report_header, connective}
      4) Missing key → KeyError (converted to exit 2 in run())
      5) connective stored as-is after stripping outer quotes
    """
    root = Path(__file__).parent.parent.parent / f"skills/whoami/templates/axes.{locale}.md"
    txt = root.read_text(encoding="utf-8")
    m = re.search(rf"(?m)^## {re.escape(axis)}$\n((?:- .+\n?)+)", txt)
    if not m:
        raise KeyError(f"axis section missing: {axis}")
    kv = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"- ([a-z_]+): (.*)$", line)
        if mm:
            v = mm.group(2)
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            kv[mm.group(1)] = v
    required = {"label", "hitl_question", "report_header", "connective"}
    missing = required - kv.keys()
    if missing:
        raise KeyError(f"{axis}: missing {missing}")
    return kv


def _render_block(out: dict, tpl: dict) -> str:
    """Assemble HITL text block (B.7 spec).

    Output format (UTF-8, LF-terminated, single trailing newline):
      {report_header}

      {hitl_question}

      - [{session_id[:8]}] {ts} — {text}
      ...

      candidate: {candidate_claim}

      [y / n / edit]

    If insufficient_evidence=True:
      {report_header}

      [insufficient evidence]
    """
    header = tpl["report_header"]
    if out.get("insufficient_evidence"):
        return f"{header}\n\n[insufficient evidence]\n"

    lines = [header, "", tpl["hitl_question"], ""]
    for q in out.get("quotes", []):
        sid = (q.get("session_id") or "")[:8]
        ts = q.get("ts") or " "
        if not ts:
            ts = " "
        text = q.get("text") or ""
        lines.append(f"- [{sid}] {ts} — {text}")
    lines.append("")
    lines.append(f"candidate: {out.get('candidate_claim', '')}")
    lines.append("")
    lines.append("[y / n / edit]")
    lines.append("")
    return "\n".join(lines)


def collect_quotes(scan_path: Path, axis: str, signal: dict, k: int = 3) -> list:
    """Collect first-match quotes from scan.json user messages per axis key.

    Return schema (invariant):
      {"session_id": str, "text": str, "ts": str, "frequency": int, "key": str}

    Determinism rules:
      1) Key candidates sorted: frequency desc, key alpha asc (tiebreak)
      2) Session traversal: original order in scan.json (ts asc)
      3) One entry per key: first-match session, first-match message
      4) text > 200 chars → first 200 chars + U+2026 (single char, locale-invariant)
      5) Duplicate text across keys → only first key kept
      6) Result length ≤ k; fewer if keys are insufficient
      7) Exception per key → skip key, continue
    """
    try:
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    sessions = scan.get("sessions", [])

    # Axes that embed first_text directly in top_examples
    _DIRECT_AXES = frozenset({"workflow", "antipattern", "ritual"})

    if axis in _DIRECT_AXES:
        results = []
        seen_texts: set = set()
        counters = signal.get("counters", {})
        for ex in signal.get("top_examples", [])[:k]:
            ft = (ex.get("first_text") or "").strip()
            if not ft or ft in seen_texts:
                continue
            if len(ft) > 200:
                ft = ft[:200] + "\u2026"
            seen_texts.add(ft)
            key = ex.get("key", "")
            results.append({
                "session_id": ex.get("first_session_id", ""),
                "text": ft,
                "ts": ex.get("first_ts", ""),
                "frequency": counters.get(key, 0),
                "key": key,
            })
        return results

    if axis == "obsession":
        results = []
        seen_texts_obs: set = set()
        for ex in signal.get("top_preambles", [])[:k]:
            ft = (ex.get("text") or "").strip()
            if not ft or ft in seen_texts_obs:
                continue
            if len(ft) > 200:
                ft = ft[:200] + "\u2026"
            seen_texts_obs.add(ft)
            results.append({
                "session_id": ex.get("first_session_id", ""),
                "text": ft,
                "ts": ex.get("first_ts", ""),
                "frequency": ex.get("count", 0),
                "key": ft[:20],
            })
        return results

    # Build key candidates with frequency (lexicon + reaction)
    candidates: list = []
    if axis == "lexicon":
        for ex in signal.get("top_examples", [])[:k]:
            w = ex.get("word") or ""
            freq = ex.get("sessions") or 0
            if w:
                candidates.append((w, freq))
    else:
        counters_r = signal.get("counters", {})
        sorted_keys = sorted(counters_r.items(), key=lambda x: (-x[1], x[0]))
        candidates = [(k_name, v) for k_name, v in sorted_keys[:k]]

    candidates.sort(key=lambda x: (-x[1], x[0]))

    results_lr = []
    seen_texts_lr: set = set()

    for key, freq in candidates:
        if len(results_lr) >= k:
            break
        try:
            quote = _find_first_quote(sessions, axis, key)
        except Exception:
            continue
        if quote is None:
            continue
        text = quote["text"]
        if text in seen_texts_lr:
            continue
        seen_texts_lr.add(text)
        results_lr.append({
            "session_id": quote["session_id"],
            "text": text,
            "ts": quote["ts"],
            "frequency": freq,
            "key": key,
        })

    return results_lr


def _find_first_quote(sessions: list, axis: str, key: str) -> Optional[dict]:
    """Find first user-role message matching key for given axis."""
    for session in sessions:
        sid = session.get("session_id", "")
        ts = session.get("started_at", "")
        messages = session.get("messages", [])

        # For ritual: only first user message per session
        if axis == "ritual":
            for msg in messages:
                if msg.get("role") == "user":
                    text = msg.get("text", "")
                    if key.lower() in text.lower():
                        return _make_quote(sid, ts, text)
                    break
            continue

        for msg in messages:
            if msg.get("role") != "user":
                continue
            text = msg.get("text", "")
            matched = False

            if axis == "lexicon":
                if re.search(r'(?<!\w)' + re.escape(key) + r'(?!\w)', text, re.IGNORECASE):
                    matched = True
            elif axis == "reaction":
                pattern = extract.REACTION_PATTERNS.get(key)
                if pattern and pattern.search(text):
                    matched = True
            elif axis in ("workflow", "antipattern"):
                if key.lower() in text.lower():
                    matched = True
            elif axis == "obsession":
                if text.startswith(key) or key in text[:len(key) + 20]:
                    matched = True

            if matched:
                return _make_quote(sid, ts, text)

    return None


def _make_quote(session_id: str, ts: str, text: str) -> dict:
    if len(text) > 200:
        text = text[:200] + "\u2026"
    return {"session_id": session_id, "ts": ts, "text": text}


def run(name: str, locale: str, scan_path: Path,
        emit_hitl_block: bool = False) -> int:
    if name not in AXES:
        return 2
    if locale not in LOCALES:
        sys.stderr.write(f"locale must be one of {LOCALES}\n")
        return 2
    if not scan_path.exists():
        return 66

    tmp = scan_path.parent / f".axis_{name}.json"
    try:
        _EXTRACTORS[name](input_path=scan_path, out_path=tmp)
        signal = honne_io.load_cache(tmp)
    except Exception as e:
        sys.stderr.write(f"extract error: {e}\n")
        return 1

    quotes = collect_quotes(scan_path, name, signal, k=3)

    try:
        tpl = _load_template(locale, name)
    except KeyError as e:
        sys.stderr.write(f"template error: {e}\n")
        return 2

    if not quotes:
        out = {"axis": name, "quotes": [], "candidate_claim": None,
               "insufficient_evidence": True}
    else:
        candidate = tpl["connective"].join(q["text"] for q in quotes)
        out = {"axis": name, "quotes": quotes, "candidate_claim": candidate,
               "insufficient_evidence": False}

    if emit_hitl_block:
        sys.stdout.write(_render_block(out, tpl))
    else:
        json.dump(out, sys.stdout, ensure_ascii=False)
    return 0


def validate(text: str, locale: str,
             skip_if_overlaps: Optional[str] = None) -> int:
    """Validate a candidate claim text.

    Exit codes:
      0  pass
      2  forbidden phrase / len < 8 / unknown locale / forbidden.json parse fail
      3  skip_if_overlaps match (past rejection reappears)
    """
    if locale not in LOCALES:
        return 2
    root = Path(__file__).parent.parent.parent / "skills/whoami/templates/forbidden.json"
    try:
        forbidden = json.loads(root.read_text())[locale]
    except Exception:
        return 2
    if len(text.strip()) < 8:
        return 2
    for phrase in forbidden:
        if phrase in text:
            return 2
    if skip_if_overlaps and skip_if_overlaps.strip() and skip_if_overlaps.strip() in text:
        return 3
    return 0
