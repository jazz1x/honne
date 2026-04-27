import json
import re
import subprocess
import sys
from pathlib import Path


def precommit() -> int:
    """Pre-commit hook: validate SKILL.md frontmatter and marketplace.json."""
    # Get staged files
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
            capture_output=True,
            text=True,
        )
        files = [f for f in result.stdout.strip().split("\n") if f]
    except Exception:
        print("Pre-commit passed")
        return 0

    for file in files:
        # Validate SKILL.md frontmatter
        if file.endswith("SKILL.md"):
            path = Path(file)
            if not path.exists():
                continue

            with open(path) as f:
                content = f.read()

            if not content.startswith("---"):
                print(f"error: {file} missing frontmatter", file=sys.stderr)
                return 1

            match = re.search(r'^name:\s*([^\n]+)', content, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if ":" in name:
                    print(f"error: {file} name contains ':': {name}", file=sys.stderr)
                    return 1

        # Validate marketplace.json — block relative source references
        if file.endswith("marketplace.json"):
            path = Path(file)
            if not path.exists():
                continue

            try:
                with open(path) as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"error: {file} invalid JSON: {e}", file=sys.stderr)
                return 1

            plugins = data if isinstance(data, list) else data.get("plugins", [])
            for plugin in plugins:
                source = plugin.get("source", "")
                if source.startswith("./") or source == ".":
                    print(
                        f"error: {file} plugin '{plugin.get('name', '?')}' uses "
                        f"relative source '{source}' — publish to a registry URL first",
                        file=sys.stderr,
                    )
                    return 1

    print("Pre-commit passed")
    return 0


if __name__ == "__main__":
    sys.exit(precommit())
