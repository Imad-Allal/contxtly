"""One-shot import: modal_particles.json → Postgres.

Curated set of German modal particles (Modalpartikeln) with per-sentence-type
pragmatic readings. The list is closed and stable; any additions go through
this same JSON → import pipeline.

Run:
    cd backend
    python -m scripts.seed_modal_particles
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
SEED_PATH = Path(__file__).parent / "seed_data" / "modal_particles.json"


def main() -> int:
    if not SEED_PATH.exists():
        log.error("Missing %s", SEED_PATH)
        return 2

    with SEED_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    rows = [
        {
            "particle": e["particle"],
            "sentence_type": e["sentence_type"],
            "reading": e["reading"],
            "source": SOURCE,
        }
        for e in data.get("particles", [])
    ]

    db = get_db()
    db.table("german_modal_particle").upsert(
        rows, on_conflict="particle,sentence_type"
    ).execute()
    log.info("Done. %d modal particle rows upserted.", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
