import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Union


def extract_lexicon(input_path: Union[Path, str], out_path: Union[Path, str], top: int = 50, min_sessions: int = 3) -> int:
    """Extract word frequency from user messages.

    Tokenize user message text, count word frequency across sessions.
    Return top N words that appear in min_sessions or more different sessions.
    """
    input_path, out_path = Path(input_path), Path(out_path)

    # Load scan.json
    try:
        with open(input_path) as f:
            scan_data = json.load(f)
    except Exception:
        return 1

    sessions = scan_data.get("sessions", [])
    if not sessions:
        return 2

    # Tokenize all user messages
    word_sessions = {}  # {word: set(session_ids)}
    word_count = Counter()

    for session in sessions:
        session_id = session.get("session_id")
        messages = session.get("messages", [])

        for msg in messages:
            if msg.get("role") != "user":
                continue

            text = msg.get("text", "")
            for word in _tokenize(text):
                word_count[word] += 1
                if word not in word_sessions:
                    word_sessions[word] = set()
                word_sessions[word].add(session_id)

    # Filter by min_sessions
    filtered_words = {
        word: count for word, count in word_count.items()
        if len(word_sessions[word]) >= min_sessions
    }

    # Top N
    top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:top]

    result = {
        "axis": "lexicon",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "counters": dict(top_words),
        "top_examples": [{"word": word, "sessions": len(word_sessions[word])} for word, _ in top_words],
        "session_coverage": {"total_sessions": len(sessions), "matched_sessions": len(word_sessions)},
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


def extract_obsession(input_path: Union[Path, str], out_path: Union[Path, str]) -> int:
    """Detect preamble repetition + language split (ko/en)."""
    input_path, out_path = Path(input_path), Path(out_path)

    try:
        with open(input_path) as f:
            scan_data = json.load(f)
    except Exception:
        return 1

    sessions = scan_data.get("sessions", [])
    if not sessions:
        return 2

    # Preamble hashing (first user message)
    preamble_hashes = Counter()
    preamble_first: dict = {}  # hash_val → {text, session_id, ts}
    lang_split = {"ko": 0, "en": 0}
    ko_msg_avg = []
    en_msg_avg = []

    for session in sessions:
        messages = session.get("messages", [])
        sid = session.get("session_id", "")
        ts = session.get("started_at", "")

        # First user message
        for msg in messages:
            if msg.get("role") == "user":
                text = msg.get("text", "")
                first_10_lines = "\n".join(text.split("\n")[:10])
                preamble_hash = hash(first_10_lines) % (10 ** 10)
                preamble_hashes[preamble_hash] += 1
                if preamble_hash not in preamble_first:
                    preamble_first[preamble_hash] = {
                        "text": first_10_lines,
                        "first_session_id": sid,
                        "first_ts": ts,
                    }
                break

        # Language split
        user_msgs = [msg for msg in messages if msg.get("role") == "user"]
        full_text = " ".join([msg.get("text", "") for msg in user_msgs])

        ko_count = sum(1 for c in full_text if unicodedata.category(c).startswith("L") and ord(c) >= 0xAC00)
        total_alpha = sum(1 for c in full_text if unicodedata.category(c).startswith("L"))

        if total_alpha > 0 and ko_count / total_alpha >= 0.3:
            lang_split["ko"] += 1
            ko_msg_avg.append(len(user_msgs))
        else:
            lang_split["en"] += 1
            en_msg_avg.append(len(user_msgs))

    # Top preambles — no threshold, top 5 by frequency
    top_preambles = [
        {
            "hash": str(hash_val),
            "count": count,
            "text": preamble_first.get(hash_val, {}).get("text", ""),
            "first_session_id": preamble_first.get(hash_val, {}).get("first_session_id", ""),
            "first_ts": preamble_first.get(hash_val, {}).get("first_ts", ""),
        }
        for hash_val, count in preamble_hashes.most_common(5)
    ]

    result = {
        "axis": "obsession",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "counters": {
            "language_split": lang_split,
            "avg_messages_ko": round(sum(ko_msg_avg) / len(ko_msg_avg), 2) if ko_msg_avg else 0,
            "avg_messages_en": round(sum(en_msg_avg) / len(en_msg_avg), 2) if en_msg_avg else 0,
        },
        "top_preambles": top_preambles,
        "session_coverage": {"total_sessions": len(sessions), "matched_sessions": len([s for s in sessions if lang_split["ko"] or lang_split["en"]])},
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


def extract_reaction(input_path: Union[Path, str], out_path: Union[Path, str]) -> int:
    """Detect user reaction patterns to assistant output."""
    input_path, out_path = Path(input_path), Path(out_path)

    try:
        with open(input_path) as f:
            scan_data = json.load(f)
    except Exception:
        return 1

    sessions = scan_data.get("sessions", [])
    if not sessions:
        return 2

    counters = {"correction": 0, "scope_cut": 0, "deepen": 0, "approval": 0}
    patterns = REACTION_PATTERNS

    matched_sessions = set()

    for session in sessions:
        messages = session.get("messages", [])
        session_id = session.get("session_id")

        for msg in messages:
            if msg.get("role") != "user":
                continue

            text = msg.get("text", "").lower()

            for pattern_name, pattern_re in patterns.items():
                if pattern_re.search(text):
                    counters[pattern_name] += 1
                    matched_sessions.add(session_id)

    result = {
        "axis": "reaction",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "counters": counters,
        "top_examples": [],
        "session_coverage": {"total_sessions": len(sessions), "matched_sessions": len(matched_sessions)},
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


def extract_workflow(input_path: Union[Path, str], out_path: Union[Path, str]) -> int:
    """Detect work initiation styles."""
    input_path, out_path = Path(input_path), Path(out_path)

    try:
        with open(input_path) as f:
            scan_data = json.load(f)
    except Exception:
        return 1

    sessions = scan_data.get("sessions", [])
    if not sessions:
        return 2

    counters = {"code_first": 0, "question_driven": 0, "multi_file_scope": 0, "small_targeted": 0}
    matched_sessions = set()
    first_examples: dict = {}  # key → {first_text, first_session_id, first_ts}

    for session in sessions:
        messages = session.get("messages", [])
        session_id = session.get("session_id")
        ts = session.get("started_at", "")

        for msg in messages:
            if msg.get("role") != "user":
                continue

            text = msg.get("text", "")
            first_2_lines = "\n".join(text.split("\n")[:2])

            # code_first
            if "```" in first_2_lines or re.search(r'(\/.\/|\.py|\.ts|\.js|\.go|\.rs)', first_2_lines):
                counters["code_first"] += 1
                matched_sessions.add(session_id)
                if "code_first" not in first_examples:
                    first_examples["code_first"] = {"first_text": text, "first_session_id": session_id, "first_ts": ts}

            # question_driven
            if "?" in text or re.search(r'(어떻게|왜|what|why|how)', first_2_lines, re.IGNORECASE):
                counters["question_driven"] += 1
                matched_sessions.add(session_id)
                if "question_driven" not in first_examples:
                    first_examples["question_driven"] = {"first_text": text, "first_session_id": session_id, "first_ts": ts}

            # multi_file_scope
            paths = re.findall(r'(/[\w/.-]+|[\w/.-]+\.\w+)', text)
            if len(set(paths)) >= 2:
                counters["multi_file_scope"] += 1
                matched_sessions.add(session_id)
                if "multi_file_scope" not in first_examples:
                    first_examples["multi_file_scope"] = {"first_text": text, "first_session_id": session_id, "first_ts": ts}

            # small_targeted
            single_path_match = len([p for p in paths if "/" in p or "." in p]) == 1
            if single_path_match and (re.search(r'\w+\(', text) or re.search(r'line \d+', text)):
                counters["small_targeted"] += 1
                matched_sessions.add(session_id)
                if "small_targeted" not in first_examples:
                    first_examples["small_targeted"] = {"first_text": text, "first_session_id": session_id, "first_ts": ts}

    top_examples = [
        {"key": k, **v}
        for k, v in sorted(first_examples.items(), key=lambda x: -counters.get(x[0], 0))
    ]

    result = {
        "axis": "workflow",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "counters": counters,
        "top_examples": top_examples,
        "session_coverage": {"total_sessions": len(sessions), "matched_sessions": len(matched_sessions)},
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


def extract_ritual(input_path: Union[Path, str], out_path: Union[Path, str]) -> int:
    """Detect session opening styles."""
    input_path, out_path = Path(input_path), Path(out_path)

    try:
        with open(input_path) as f:
            scan_data = json.load(f)
    except Exception:
        return 1

    sessions = scan_data.get("sessions", [])
    if not sessions:
        return 2

    counters = {"direct_command": 0, "question": 0, "task_description": 0}
    first_examples: dict = {}  # key → {first_text, first_session_id, first_ts}

    for session in sessions:
        messages = session.get("messages", [])
        session_id = session.get("session_id", "")
        ts = session.get("started_at", "")

        # First user message
        for msg in messages:
            if msg.get("role") == "user":
                text = msg.get("text", "").strip()

                if re.match(r'^(해봐|실행|run|do|execute|make|build)\b', text, re.IGNORECASE):
                    key = "direct_command"
                elif "?" in text or re.match(r'^(어떻게|뭐|무엇|what|why|how)', text, re.IGNORECASE):
                    key = "question"
                else:
                    key = "task_description"

                counters[key] += 1
                if key not in first_examples:
                    first_examples[key] = {"first_text": text, "first_session_id": session_id, "first_ts": ts}
                break

    top_examples = [
        {"key": k, **v}
        for k, v in sorted(first_examples.items(), key=lambda x: -counters.get(x[0], 0))
    ]

    result = {
        "axis": "ritual",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "counters": counters,
        "top_examples": top_examples,
        "session_coverage": {"total_sessions": len(sessions), "matched_sessions": len(sessions)},
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


def extract_antipattern(input_path: Union[Path, str], out_path: Union[Path, str]) -> int:
    """Detect request quality anti-patterns."""
    input_path, out_path = Path(input_path), Path(out_path)

    try:
        with open(input_path) as f:
            scan_data = json.load(f)
    except Exception:
        return 1

    sessions = scan_data.get("sessions", [])
    if not sessions:
        return 2

    counters = {"overspec": 0, "repeat_same_request": 0}
    matched_sessions = set()
    first_examples: dict = {}  # key → {first_text, first_session_id, first_ts}

    overspec_pattern = re.compile(r'(반드시|무조건|정확히|exactly|must|ALWAYS|NEVER|strictly|in this exact order)', re.IGNORECASE)

    for session in sessions:
        messages = session.get("messages", [])
        session_id = session.get("session_id")
        ts = session.get("started_at", "")

        # overspec
        for msg in messages:
            if msg.get("role") == "user":
                text = msg.get("text", "")
                if overspec_pattern.search(text):
                    counters["overspec"] += 1
                    matched_sessions.add(session_id)
                    if "overspec" not in first_examples:
                        first_examples["overspec"] = {"first_text": text, "first_session_id": session_id, "first_ts": ts}

        # repeat_same_request
        normalized_texts = set()
        for msg in messages:
            if msg.get("role") == "user":
                text = msg.get("text", "")
                normalized = re.sub(r'\s+', ' ', text).lower()
                if normalized in normalized_texts:
                    counters["repeat_same_request"] += 1
                    matched_sessions.add(session_id)
                    if "repeat_same_request" not in first_examples:
                        first_examples["repeat_same_request"] = {"first_text": text, "first_session_id": session_id, "first_ts": ts}
                    break
                normalized_texts.add(normalized)

    top_examples = [
        {"key": k, **v}
        for k, v in sorted(first_examples.items(), key=lambda x: -counters.get(x[0], 0))
    ]

    result = {
        "axis": "antipattern",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "counters": counters,
        "top_examples": top_examples,
        "session_coverage": {"total_sessions": len(sessions), "matched_sessions": len(matched_sessions)},
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


def extract_signature(input_path: Union[Path, str], out_path: Union[Path, str]) -> int:
    """Detect characteristic positive patterns — decisive closure and targeted requests."""
    input_path, out_path = Path(input_path), Path(out_path)

    try:
        with open(input_path) as f:
            scan_data = json.load(f)
    except Exception:
        return 1

    sessions = scan_data.get("sessions", [])
    if not sessions:
        return 2

    counters: dict = {"decisive_close": 0, "targeted_request": 0}
    matched_sessions: set = set()
    first_examples: dict = {}

    # ≤5-word affirmative/closure messages (instruction verbs like push/merge excluded)
    decisive_pattern = re.compile(
        r'\b(ok|okay|ㅇㅇ|네|좋아|됐어|됩니다|완료|done|go ahead|proceed|fix all|그래|맞아|진행해|처리해|알겠어|확인)\b',
        re.IGNORECASE,
    )
    # references a specific file path (with extension) or line:col pattern
    targeted_pattern = re.compile(
        r'\b\w[\w/.-]*\.(py|ts|js|go|sh|md|json|yaml|yml|toml)(:\d+)?\b'
    )

    for session in sessions:
        messages = session.get("messages", [])
        session_id = session.get("session_id")
        ts = session.get("started_at", "")

        for msg in messages:
            if msg.get("role") != "user":
                continue
            text = msg.get("text", "").strip()
            if not text:
                continue

            word_count = len(text.split())
            if word_count <= 5 and decisive_pattern.search(text):
                counters["decisive_close"] += 1
                matched_sessions.add(session_id)
                if "decisive_close" not in first_examples:
                    first_examples["decisive_close"] = {
                        "first_text": text, "first_session_id": session_id, "first_ts": ts,
                    }

            if targeted_pattern.search(text):
                counters["targeted_request"] += 1
                matched_sessions.add(session_id)
                if "targeted_request" not in first_examples:
                    first_examples["targeted_request"] = {
                        "first_text": text, "first_session_id": session_id, "first_ts": ts,
                    }

    top_examples = [
        {"key": k, **v}
        for k, v in sorted(first_examples.items(), key=lambda x: -counters.get(x[0], 0))
    ]

    result = {
        "axis": "signature",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "counters": counters,
        "top_examples": top_examples,
        "session_coverage": {"total_sessions": len(sessions), "matched_sessions": len(matched_sessions)},
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


REACTION_PATTERNS: dict = {
    "correction": re.compile(r'(아님|아니|틀렸|잘못|wrong|incorrect|not (right|correct))', re.IGNORECASE),
    "scope_cut":  re.compile(r'(만|그만|stop|only|just|대신|하지마|skip)', re.IGNORECASE),
    "deepen":     re.compile(r'(더|추가|계속|확장|deeper|more|continue|expand|elaborate)', re.IGNORECASE),
    "approval":   re.compile(r'(좋|맞|맞아|완벽|good|perfect|correct|nice|yes[.!]?\s*$)', re.IGNORECASE),
}


_STOPWORDS = frozenset({
    # English function words
    "the","a","an","and","or","but","if","so","not","no","yes",
    "in","on","at","to","of","for","with","by","from","as","into","onto",
    "is","are","was","were","be","been","being","am",
    "have","has","had","having","do","does","did","doing","done",
    "will","would","should","can","could","may","might","must","shall",
    "this","that","these","those","there","here","then","than","when","where","why","how","what","who","which",
    "i","you","he","she","it","we","they","me","him","her","us","them",
    "my","your","his","its","our","their","mine","yours","ours","theirs",
    "all","any","both","each","few","more","most","other","some","such","only","own","same","very",
    "out","up","down","over","under","off","about","again","also","just",
    # Code/file extensions and common technical noise
    "md","py","js","ts","tsx","jsx","sh","json","jsonl","yml","yaml","txt","html","css",
    "src","lib","bin","dir","tmp","log","logs","conf","env","docs","doc","file","files","path","paths","code",
    # Common Korean particles/fillers (when accidentally tokenized standalone)
    "그","이","저","것","수","등","및","좀","더","잘","또",
    # Common Japanese fillers (when standalone)
    "の","は","が","を","に","で","と","も","から","まで",
})

_TOKEN_RE = re.compile(r'[^\W_\d]+', re.UNICODE)


def _tokenize(text: str) -> Iterator[str]:
    """Tokenize text to lowercase words (Unicode-aware).

    Filters: min length 3, alphabetic only (no digits), not in stopword set.
    """
    for match in _TOKEN_RE.finditer(text):
        tok = match.group().lower()
        if len(tok) < 3 or tok in _STOPWORDS:
            continue
        yield tok
