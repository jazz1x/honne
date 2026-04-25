from pathlib import Path
from typing import Union
import json
import sys


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


def render_personas(
    synthesis_path: Union[Path, str],
    persona_path: Union[Path, str],
    locale: str,
    out_dir: Union[Path, str],
) -> int:
    """Render .honne/personas/{antipattern,signature,judge}.md from synthesis.

    Exit codes:
      0: success
      2: template error (missing locale template)
      66: missing/malformed synthesis or persona.json
    """
    VALID_LOCALES = {"ko", "en", "jp"}

    if locale not in VALID_LOCALES:
        print(f"error: invalid locale '{locale}'. valid: ko, en, jp", file=sys.stderr)
        return 2

    synthesis_path = Path(synthesis_path)
    persona_path = Path(persona_path)
    out_dir = Path(out_dir)

    # 1. Load + validate synthesis JSON
    if not synthesis_path.exists():
        print(f"error: synthesis file not found: {synthesis_path}", file=sys.stderr)
        return 66

    try:
        with open(synthesis_path, "r", encoding="utf-8") as f:
            synthesis = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"error: failed to parse {synthesis_path}: {e}", file=sys.stderr)
        return 66

    # Validate synthesis schema
    if "conflict_present" not in synthesis:
        print("error: synthesis missing 'conflict_present' key", file=sys.stderr)
        return 66

    conflict_present = synthesis["conflict_present"]

    if conflict_present:
        # All three required when conflict is present
        for required_key in ("persona_antipattern", "persona_signature", "judge_system_prompt"):
            if required_key not in synthesis or synthesis[required_key] is None:
                print(f"error: synthesis missing or null '{required_key}' (required when conflict_present=true)", file=sys.stderr)
                return 66
            if required_key != "judge_system_prompt":
                persona_block = synthesis[required_key]
                for block_key in ("name", "oneliner", "system_prompt"):
                    if block_key not in persona_block:
                        print(f"error: {required_key} missing '{block_key}'", file=sys.stderr)
                        return 66
    else:
        # At most one of antipattern/signature when conflict absent
        antipattern_count = 1 if synthesis.get("persona_antipattern") is not None else 0
        signature_count = 1 if synthesis.get("persona_signature") is not None else 0
        if antipattern_count + signature_count > 1:
            print("error: conflict_present=false but multiple personas present", file=sys.stderr)
            return 66

    # 2. Load persona.json
    if not persona_path.exists():
        print(f"error: persona file not found: {persona_path}", file=sys.stderr)
        return 66

    # 3. Load template
    template_path = Path(__file__).parent.parent.parent / "skills" / "persona" / "templates" / "persona_render.md"
    if not template_path.exists():
        print(f"error: template not found: {template_path}", file=sys.stderr)
        return 2

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except OSError as e:
        print(f"error: failed to read template: {e}", file=sys.stderr)
        return 2

    # 4. Create out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # 5. Render persona files
    if synthesis.get("persona_antipattern") is None and synthesis.get("persona_signature") is None:
        print("warn: no personas to render (both null)", file=sys.stderr)
        return 0

    if synthesis.get("persona_antipattern") is not None:
        antipattern = synthesis["persona_antipattern"]
        rendered = template.format(
            name=antipattern["name"],
            oneliner=antipattern["oneliner"],
            system_prompt=antipattern["system_prompt"],
        )
        (out_dir / "antipattern.md").write_text(rendered, encoding="utf-8")

    if synthesis.get("persona_signature") is not None:
        signature = synthesis["persona_signature"]
        rendered = template.format(
            name=signature["name"],
            oneliner=signature["oneliner"],
            system_prompt=signature["system_prompt"],
        )
        (out_dir / "signature.md").write_text(rendered, encoding="utf-8")

    # 6. Write judge as-is (no template wrap)
    if synthesis.get("judge_system_prompt") is not None:
        (out_dir / "judge.md").write_text(synthesis["judge_system_prompt"], encoding="utf-8")

    # 7. Return success
    return 0
