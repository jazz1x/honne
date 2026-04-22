"""pytest shared config — makes scripts/ importable and exposes fixture paths."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"

# Make scripts/_redact.py and scripts/_tokenize.py importable as modules.
sys.path.insert(0, str(SCRIPTS_DIR))
