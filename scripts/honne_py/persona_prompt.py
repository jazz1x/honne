from pathlib import Path
from typing import Union, Dict, Any, Optional
import json
import sys
import re


def build_conflict_payload(persona_path: Union[Path, str], locale: str) -> dict:
    """Build CONFLICT_PAYLOAD from persona.json for synthesis.

    Extracts antipattern + signature axes and supporting axes.
    Returns ConflictPayload as dict.

    Exit codes:
      66: persona.json missing
      2: locale invalid
    """
    VALID_LOCALES = {"ko", "en", "jp"}
    AXES = ("lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern", "signature")

    if locale not in VALID_LOCALES:
        print(f"error: invalid locale '{locale}'. valid: ko, en, jp", file=sys.stderr)
        sys.exit(2)

    persona_path = Path(persona_path)
    if not persona_path.exists():
        print(f"error: persona file not found: {persona_path}", file=sys.stderr)
        sys.exit(66)

    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            persona = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"error: failed to parse {persona_path}: {e}", file=sys.stderr)
        sys.exit(66)

    axes = persona.get("axes", {})

    def _axis_summary(axis_data):
        """Convert axis data to summary dict, or None if absent."""
        if axis_data is None:
            return None
        return {
            "claim": axis_data.get("claim"),
            "explanation": axis_data.get("explanation"),
            "evidence_strength": axis_data.get("evidence_strength", 0.0),
        }

    antipattern = _axis_summary(axes.get("antipattern"))
    signature = _axis_summary(axes.get("signature"))
    conflict_present = antipattern is not None and signature is not None

    payload = {
        "locale": locale,
        "antipattern": antipattern,
        "signature": signature,
        "supporting_axes": {},
        "conflict_present": conflict_present,
    }

    # Add remaining 5 axes as context
    for axis in AXES:
        if axis not in ("antipattern", "signature"):
            axis_data = axes.get(axis)
            if axis_data is not None:
                payload["supporting_axes"][axis] = _axis_summary(axis_data)

    return payload


def render_persona_prompt(
    synthesis_path: Union[Path, str],
    persona_path: Union[Path, str],
    locale: str,
    out_path: Union[Path, str],
) -> int:
    """Render .honne/persona-prompt.md from synthesis + persona data.

    Reads persona-synthesis.json + persona.json.
    Applies persona_prompt.<locale>.md template.
    Writes to out_path.

    Exit codes:
      0: success
      2: template error
      66: missing file
    """
    VALID_LOCALES = {"ko", "en", "jp"}

    synthesis_path = Path(synthesis_path)
    persona_path = Path(persona_path)
    out_path = Path(out_path)

    # Load synthesis
    if not synthesis_path.exists():
        print(f"error: synthesis file not found: {synthesis_path}", file=sys.stderr)
        return 66

    try:
        with open(synthesis_path, "r", encoding="utf-8") as f:
            synthesis = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"error: failed to parse {synthesis_path}: {e}", file=sys.stderr)
        return 66

    required_keys = {"verdict", "character_oneliner", "system_prompt", "conflict_present"}
    missing = required_keys - synthesis.keys()
    if missing:
        print(f"error: synthesis missing required keys: {sorted(missing)}", file=sys.stderr)
        return 66

    if synthesis.get("conflict_present"):
        debate = synthesis.get("debate")
        if not isinstance(debate, dict):
            print("error: conflict_present=true but debate field missing or invalid", file=sys.stderr)
            return 66
        debate_required = {"antipattern_voice", "signature_voice", "resolution"}
        debate_missing = debate_required - debate.keys()
        if debate_missing:
            print(f"error: debate missing required keys: {sorted(debate_missing)}", file=sys.stderr)
            return 66

    # Load persona
    if not persona_path.exists():
        print(f"error: persona file not found: {persona_path}", file=sys.stderr)
        return 66

    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            persona = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"error: failed to parse {persona_path}: {e}", file=sys.stderr)
        return 66

    # Load template
    tpl = _load_persona_prompt_template(locale)
    if not tpl:
        print(f"error: template missing for locale {locale}", file=sys.stderr)
        return 2

    # Extract data
    character_oneliner = synthesis.get("character_oneliner", "")
    verdict = synthesis.get("verdict", "")
    system_prompt = synthesis.get("system_prompt", "")

    axes = persona.get("axes", {})
    signature_claim = ""
    antipattern_claim = ""

    if axes.get("signature") is not None:
        signature_claim = axes["signature"].get("claim", "")
    if axes.get("antipattern") is not None:
        antipattern_claim = axes["antipattern"].get("claim", "")

    # Render from template
    output = tpl["header"]
    output = output.replace("{character_oneliner}", character_oneliner)

    # Who you are section
    output += "\n\n" + tpl["who_you_are"]
    output = output.replace("{verdict}", verdict)

    # Behavioral signature section (only if present)
    if signature_claim:
        output += "\n\n" + tpl["behavioral_signature"]
        output = output.replace("{signature_claim}", signature_claim)

    # Watch out for section (only if present)
    if antipattern_claim:
        output += "\n\n" + tpl["watch_out_for"]
        output = output.replace("{antipattern_claim}", antipattern_claim)

    # Debate section — validation at the top guarantees the dict + 3 required keys
    # exist whenever conflict_present is true.
    if synthesis.get("conflict_present"):
        debate = synthesis["debate"]
        output += "\n\n" + tpl["debate"]
        output = output.replace("{debate_antipattern_voice}", debate["antipattern_voice"])
        output = output.replace("{debate_signature_voice}", debate["signature_voice"])
        output = output.replace("{debate_resolution}", debate["resolution"])

    # System prompt section
    output += "\n\n" + tpl["system_prompt_section"]
    output = output.replace("{system_prompt}", system_prompt)

    # Activation directive — template load enforces this section's presence.
    output += "\n\n" + tpl["activation_directive"]

    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    return 0


def _load_persona_prompt_template(locale: str) -> Optional[Dict[str, str]]:
    """Parse persona_prompt.<locale>.md for required sections."""
    root = Path(__file__).parent.parent.parent / f"skills/persona/templates/persona_prompt.{locale}.md"
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

    # Verify required sections (debate + activation_directive added in 0.0.2)
    required = {
        "header", "who_you_are", "behavioral_signature",
        "watch_out_for", "debate", "system_prompt_section", "activation_directive",
    }
    if not required.issubset(sections.keys()):
        return None
    return sections
