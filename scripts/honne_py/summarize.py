from pathlib import Path
from typing import Dict
import re


def _load_summary_template(locale: str, axis: str) -> Dict[str, str]:
    """Parse axes.<locale>.md for summary_template.* keys in axis section.

    Returns dict with flat keys: {"label": ..., "item_sep": ..., "empty": ...}
    """
    root = Path(__file__).parent.parent.parent / f"skills/whoami/templates/axes.{locale}.md"
    txt = root.read_text(encoding="utf-8")
    m = re.search(rf"(?m)^## {re.escape(axis)}$\n((?:- .+\n?)+)", txt)
    if not m:
        raise KeyError(f"axis section missing: {axis}")
    kv = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"- ([a-z_][a-z_.]*): (.*)$", line)
        if mm:
            v = mm.group(2)
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            kv[mm.group(1)] = v
    required = {"summary_template.label", "summary_template.item_sep", "summary_template.empty"}
    missing = required - kv.keys()
    if missing:
        raise KeyError(f"{axis}/{locale}: missing {missing}")
    return kv


def summarize_lexicon(signal: dict, locale: str) -> str:
    """Top examples (words) sorted by frequency desc, word asc on tie.
    Max 5 items. Format: '{label}: word1(freq1), word2(freq2), ...'
    Empty signal or all word=="" → "".
    """
    tpl = _load_summary_template(locale, "lexicon")
    label = tpl["summary_template.label"]
    sep = tpl["summary_template.item_sep"]

    examples = signal.get("top_examples", [])
    if not examples:
        return ""

    # Filter out empty words, deduplicate, sort by freq desc then word asc
    items = []
    seen = set()
    for ex in examples:
        word = ex.get("word", "").strip()
        if not word or word in seen:
            continue
        seen.add(word)
        freq = ex.get("sessions", 0)
        items.append((word, freq))

    if not items:
        return ""

    items.sort(key=lambda x: (-x[1], x[0]))
    items = items[:5]
    result = sep.join(f"{word}({freq})" for word, freq in items)
    return f"{label}: {result}"


def summarize_reaction(signal: dict, locale: str) -> str:
    """Counters sorted by frequency desc, key asc on tie.
    Max 5 items. Format: '{label}: key1(freq1), key2(freq2), ...'
    """
    tpl = _load_summary_template(locale, "reaction")
    label = tpl["summary_template.label"]
    sep = tpl["summary_template.item_sep"]

    counters = signal.get("counters", {})
    if not counters:
        return ""

    items = [(key, count) for key, count in counters.items()]
    items.sort(key=lambda x: (-x[1], x[0]))
    items = items[:5]
    result = sep.join(f"{key}({count})" for key, count in items)
    return f"{label}: {result}"


def summarize_workflow(signal: dict, locale: str) -> str:
    """Top examples (workflow steps) sorted by frequency desc, key asc on tie.
    Max 3 items (workflows are longer). Format: '{label}: step1 → step2 → ...'
    """
    tpl = _load_summary_template(locale, "workflow")
    label = tpl["summary_template.label"]
    sep = tpl["summary_template.item_sep"]

    counters = signal.get("counters", {})
    if not counters:
        return ""

    items = [(key, count) for key, count in counters.items()]
    items.sort(key=lambda x: (-x[1], x[0]))
    items = items[:3]
    result = sep.join(key for key, _ in items)
    return f"{label}: {result}"


def summarize_obsession(signal: dict, locale: str) -> str:
    """Top preambles (first 40 chars) sorted by count desc, text asc on tie.
    Max 3 items. Format: '{label}: "text40…"(count) / "text40…"(count) / ...'
    """
    tpl = _load_summary_template(locale, "obsession")
    label = tpl["summary_template.label"]

    preambles = signal.get("top_preambles", [])
    if not preambles:
        return ""

    items = []
    seen = set()
    for p in preambles:
        text = p.get("text", "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        count = p.get("count", 0)
        items.append((text, count))

    if not items:
        return ""

    items.sort(key=lambda x: (-x[1], x[0]))
    items = items[:3]
    parts = []
    for text, count in items:
        preview = text[:40] + ("…" if len(text) > 40 else "")
        parts.append(f'"{preview}"({count})')
    return f"{label}: {' / '.join(parts)}"


def summarize_ritual(signal: dict, locale: str) -> str:
    """Top examples (first 60 chars) sorted by frequency desc, key asc on tie.
    Max 3 items. Format: '{label}: "text60…"(freq) / "text60…"(freq) / ...'

    Frequency comes from signal['counters'][key] — extract_ritual stores
    the count there, not on the top_examples entries themselves.
    """
    tpl = _load_summary_template(locale, "ritual")
    label = tpl["summary_template.label"]

    examples = signal.get("top_examples", [])
    if not examples:
        return ""

    counters = signal.get("counters", {})
    items = []
    seen = set()
    for ex in examples:
        first_text = ex.get("first_text", "").strip()
        if not first_text or first_text in seen:
            continue
        seen.add(first_text)
        freq = counters.get(ex.get("key", ""), 0)
        items.append((first_text, freq))

    if not items:
        return ""

    items.sort(key=lambda x: (-x[1], x[0]))
    items = items[:3]
    parts = []
    for text, freq in items:
        preview = text[:60] + ("…" if len(text) > 60 else "")
        parts.append(f'"{preview}"({freq})')
    return f"{label}: {' / '.join(parts)}"


def summarize_signature(signal: dict, locale: str) -> str:
    """Non-zero positive counters sorted by frequency desc, key asc on tie.
    Max 5 items. Format: '{label}: key1(freq1), key2(freq2), ...'
    """
    tpl = _load_summary_template(locale, "signature")
    label = tpl["summary_template.label"]
    sep = tpl["summary_template.item_sep"]

    counters = signal.get("counters", {})
    items = [(key, count) for key, count in counters.items() if count > 0]
    if not items:
        return ""

    items.sort(key=lambda x: (-x[1], x[0]))
    items = items[:5]
    result = sep.join(f"{key}({count})" for key, count in items)
    return f"{label}: {result}"


def summarize_antipattern(signal: dict, locale: str) -> str:
    """Counters sorted by frequency desc, key asc on tie.
    Max 5 items. Format: '{label}: key1(freq1), key2(freq2), ...'
    (Same as reaction but different label.)
    """
    tpl = _load_summary_template(locale, "antipattern")
    label = tpl["summary_template.label"]
    sep = tpl["summary_template.item_sep"]

    counters = signal.get("counters", {})
    if not counters:
        return ""

    items = [(key, count) for key, count in counters.items()]
    items.sort(key=lambda x: (-x[1], x[0]))
    items = items[:5]
    result = sep.join(f"{key}({count})" for key, count in items)
    return f"{label}: {result}"
