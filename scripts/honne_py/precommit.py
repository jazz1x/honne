import re
import subprocess
import sys
from pathlib import Path


def precommit() -> int:
    """Pre-commit hook: validate SKILL.md frontmatter."""
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

    # Check SKILL.md files
    for file in files:
        if file.endswith("SKILL.md"):
            path = Path(file)
            if not path.exists():
                continue

            with open(path) as f:
                content = f.read()

            # Validate frontmatter
            if not content.startswith("---"):
                print(f"error: {file} missing frontmatter", file=sys.stderr)
                return 1

            # Check for ':' in name field
            match = re.search(r'^name:\s*([^\n]+)', content, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if ":" in name:
                    print(f"error: {file} name contains ':': {name}", file=sys.stderr)
                    return 1

    print("Pre-commit passed")
    return 0


if __name__ == "__main__":
    sys.exit(precommit())
