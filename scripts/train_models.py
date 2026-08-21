"""FixtureIQ model-training entry point.

Stage 5 currently trains the outcome model. Stage 6 will extend this wrapper to
train the goal/scoreline models as well.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.models.train_outcome_model import main


if __name__ == "__main__":
    main()
