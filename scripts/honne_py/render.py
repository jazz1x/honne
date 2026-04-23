from pathlib import Path
from typing import Union, Dict, List, Any, Optional
import json
import sys
import re


def render_persona(
    claims_path: Union[Path, str],
    scope: str,
    locale: str,
    run_id: str,
    now: str,
    out_path: Union[Path, str],
    narrative_path: Optional[Union[Path, str]] = None,
) -> int:
    """Generate persona.json from claims.jsonl.

    Selection:
    - type == "claim"
    - scope matches
    - run_id matches (missing records filtered out)
    - per-axis: latest by created_at (1 per axis)

    Output persona.json schema:
      {
        "generated_at": now,
        "scope": scope,
        "locale": locale,
        "run_id": run_id,
        "axes": {
          "<axis>": {"claim": "...", "quotes": [...],
                     "evidence_strength": 0.XX, "run_ts": "..."}
                  | null
          for axis in AXES
        }
      }

    Evidence strength = min(len(quotes), 3) / 3, rounded to 2 decimals.

    Exit codes:
      0: success
      1: claims_path missing/parse error
      2: argument error (scope/locale values, now format)
    """
    AXES = ("lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern")

    try:
        claims_path = Path(claims_path)
        if not claims_path.exists():
            print(f"error: claims file not found: {claims_path}", file=sys.stderr)
            return 1

        # Parse claims.jsonl, filter by type/scope/run_id, group by axis
        axis_latest = {}
        try:
            with open(claims_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    if (record.get("type") != "claim" or
                        record.get("scope") != scope or
                        record.get("run_id") != run_id):
                        continue
                    axis = record.get("axis")
                    if axis not in AXES:
                        continue
                    # Keep latest (created_at desc = max)
                    if axis not in axis_latest or record.get("created_at") > axis_latest[axis].get("created_at"):
                        axis_latest[axis] = record
        except (json.JSONDecodeError, OSError) as e:
            print(f"error: failed to parse {claims_path}: {e}", file=sys.stderr)
            return 1

        # Build persona.json axes
        axes_out = {}
        for axis in AXES:
            if axis in axis_latest:
                rec = axis_latest[axis]
                quotes = rec.get("quotes", [])
                evidence_strength = round(min(len(quotes), 3) / 3, 2)
                axes_out[axis] = {
                    "claim": rec.get("claim"),
                    "quotes": quotes,
                    "evidence_strength": evidence_strength,
                    "run_ts": rec.get("created_at"),
                }
            else:
                axes_out[axis] = None

        persona = {
            "generated_at": now,
            "scope": scope,
            "locale": locale,
            "run_id": run_id,
            "axes": axes_out,
        }

        # Load narrative if provided
        narrative = None
        if narrative_path:
            narrative_path = Path(narrative_path)
            if narrative_path.exists():
                try:
                    with open(narrative_path, "r", encoding="utf-8") as f:
                        narrative = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    print(f"warning: failed to parse narrative {narrative_path}: {e}", file=sys.stderr)
                    narrative = None

        # Inject explanation/oneliner if narrative available
        if narrative:
            narrative_axes = narrative.get("axes", {})
            for axis in AXES:
                if axis in axes_out and axes_out[axis] is not None:
                    if axis in narrative_axes and narrative_axes[axis] is not None:
                        axes_out[axis]["explanation"] = narrative_axes[axis]
                    else:
                        axes_out[axis]["explanation"] = None
            if "oneliner" in narrative and narrative["oneliner"] is not None:
                persona["oneliner"] = narrative["oneliner"]
            else:
                persona["oneliner"] = None
        else:
            # No narrative: set all explanation/oneliner to null
            for axis in AXES:
                if axis in axes_out and axes_out[axis] is not None:
                    axes_out[axis]["explanation"] = None
            persona["oneliner"] = None

        # Write with determinism: sort_keys=True, separators, ensure_ascii=False
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(persona, f, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
            f.write("\n")
        return 0

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def render_report(
    persona_path: Union[Path, str],
    locale: str,
    out_path: Union[Path, str],
) -> int:
    """Generate docs/honne.md from persona.json.

    Template: skills/whoami/templates/report.<locale>.md

    Placeholders (all required):
      {generated_at} {scope} {locale} {run_id_short}
      {axis_header} {claim} {evidence_count}
      {quote_session} {quote_ts} {quote_text} {quote_freq}

    Unapproved axes (null) → [insufficient evidence] single line.

    Exit codes:
      0: success
      1: persona_path missing/parse, template missing
      2: argument error
    """
    AXES = ("lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern")

    try:
        persona_path = Path(persona_path)
        if not persona_path.exists():
            print(f"error: persona file not found: {persona_path}", file=sys.stderr)
            return 1

        # Parse persona.json
        try:
            with open(persona_path, "r", encoding="utf-8") as f:
                persona = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"error: failed to parse {persona_path}: {e}", file=sys.stderr)
            return 1

        # Load template
        tpl = _load_report_template(locale)
        if not tpl:
            print(f"error: template missing for locale {locale}", file=sys.stderr)
            return 1

        # Render axes
        axes = persona.get("axes", {})
        axis_renders = []
        for axis in AXES:
            axis_data = axes.get(axis)
            if axis_data is None:
                # Insufficient evidence
                axis_header = _get_axis_header(persona, axis, locale)
                block = tpl["insufficient_block"].replace("{axis_header}", axis_header)
                axis_renders.append(block)
            else:
                axis_header = _get_axis_header(persona, axis, locale)
                claim = axis_data.get("claim", "")
                quotes = axis_data.get("quotes", [])
                evidence_count = len(quotes)
                explanation = axis_data.get("explanation")

                # Render axis block
                axis_block = tpl["axis_block"]
                axis_block = axis_block.replace("{axis_header}", axis_header)
                axis_block = axis_block.replace("{claim}", claim)
                # Remove explanation line if null
                if explanation is None:
                    axis_block = _EXPLANATION_LINE_RE[locale].sub('', axis_block)
                axis_block = axis_block.replace("{axis_explanation}", explanation if explanation is not None else "")
                axis_renders.append(axis_block)

        # Assemble final output
        header = tpl["header"]
        header = header.replace("{generated_at}", persona.get("generated_at", ""))
        header = header.replace("{scope}", persona.get("scope", ""))
        header = header.replace("{locale}", persona.get("locale", ""))
        run_id_short = persona.get("run_id", "")[:8]
        header = header.replace("{run_id_short}", run_id_short)

        output = header + "\n\n" + "\n\n".join(axis_renders) + "\n"

        # Add footer if oneliner is present
        if "footer" in tpl and persona.get("oneliner") is not None:
            footer = tpl["footer"]
            footer = footer.replace("{oneliner}", persona.get("oneliner", ""))
            output += "\n" + footer

        # Always append next_actions if present in template
        if "next_actions" in tpl:
            output += "\n\n" + tpl["next_actions"]

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
        return 0

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


_EXPLANATION_LINE_RE = {
    "ko": re.compile(r'\n\n\*\*해설\*\*: \{axis_explanation\}'),
    "en": re.compile(r'\n\n\*\*Explanation\*\*: \{axis_explanation\}'),
    "jp": re.compile(r'\n\n\*\*解説\*\*: \{axis_explanation\}'),
}


def _load_report_template(locale: str) -> Dict[str, str]:
    """Parse report.<locale>.md for 5 sections: header, axis_block, quote_line, insufficient_block, footer (optional)."""
    root = Path(__file__).parent.parent.parent / f"skills/whoami/templates/report.{locale}.md"
    try:
        txt = root.read_text(encoding="utf-8")
    except (OSError, FileNotFoundError):
        return None

    # Split by ^## section_name
    sections = {}
    current_section = None
    current_content = []
    for line in txt.splitlines(keepends=True):
        m = re.match(r"^## ([a-z_]+)$", line.rstrip())
        if m:
            if current_section:
                sections[current_section] = "".join(current_content).strip("\n")
            current_section = m.group(1)
            current_content = []
        elif current_section:
            current_content.append(line)
    if current_section:
        sections[current_section] = "".join(current_content).strip("\n")

    # Verify required sections (footer, quote_line, next_actions are optional)
    required = {"header", "axis_block", "insufficient_block"}
    if not required.issubset(sections.keys()):
        return None
    return sections


def _get_axis_header(persona: dict, axis: str, locale: str) -> str:
    """Get report_header from axes.<locale>.md for given axis."""
    root = Path(__file__).parent.parent.parent / f"skills/whoami/templates/axes.{locale}.md"
    try:
        txt = root.read_text(encoding="utf-8")
    except (OSError, FileNotFoundError):
        return axis

    m = re.search(rf"(?m)^## {re.escape(axis)}$\n((?:- .+\n?)+)", txt)
    if not m:
        return axis
    for line in m.group(1).splitlines():
        mm = re.match(r"- report_header: (.*)$", line)
        if mm:
            return mm.group(1)
    return axis
