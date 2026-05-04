"""One-shot import: n_declination.json → Postgres.

The n-Deklination class is closed — these are well-documented in
canonical German grammar references and the list rarely changes.
Run after migration 015 is applied.

    cd backend
    python -m scripts.seed_n_declination
"""

import json
import logging
import sys
from pathlib import Path

from db import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

SOURCE = "curated_v1"
SEED_PATH = Path(__file__).parent / "seed_data" / "n_declination.json"


def main() -> int:
    if not SEED_PATH.exists():
        log.error("Missing %s", SEED_PATH)
        return 2

    with SEED_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    rows = [{"lemma": l, "source": SOURCE} for l in data.get("lemmas", []) if l]
    if not rows:
        log.error("No lemmas in seed file")
        return 2

    db = get_db()
    db.table("german_n_decl").upsert(rows, on_conflict="lemma").execute()
    log.info("Done. %d n-Deklination lemmas upserted.", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
