import sys
from pathlib import Path

# Ensure tests can import the app package without installing the package.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Deterministic-only tests (no live API calls) are the default so CI can run
# without credentials. Live evaluation is opt-in via `--live`.
