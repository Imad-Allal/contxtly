"""One-shot import: curated_v1.json → Postgres.

The canonical seed lives at backend/scripts/seed_data/curated_v1.json
(generated once from the original Python data files, now the source
of truth for the curated rows).

Run from backend/:
    python -m scripts.import_german_dicts

Idempotent — uses upserts on the unique constraints in migration 005.
Tags every row with source='curated_v1' so we can roll back / re-attribute
later when external seeds (Wiktionary, DWDS, …) are added.
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
BATCH = 500
SEED_PATH = Path(__file__).parent / "seed_data" / "curated_v1.json"


def _chunks(rows, n=BATCH):
    for i in range(0, len(rows), n):
        yield rows[i : i + n]


def import_nvv(db, entries: list[dict]) -> int:
    rows = [
        {
            "noun": e["noun"],
            "verb_lemma": e["verb_lemma"],
            "prep_lemma": e.get("prep_lemma"),
            "canonical": e["canonical"],
            "requires_sich": e.get("requires_sich", False),
            "source": SOURCE,
        }
        for e in entries
    ]
    inserted = 0
    for batch in _chunks(rows):
        db.table("german_nvv").upsert(
            batch, on_conflict="noun,verb_lemma,prep_lemma,requires_sich"
        ).execute()
        inserted += len(batch)
    return inserted


def import_expressions(db, entries: list[dict]) -> int:
    rows = [
        {
            "tokens": e["tokens"],
            "canonical": e["canonical"],
            "source": SOURCE,
        }
        for e in entries
    ]
    inserted = 0
    for batch in _chunks(rows):
        db.table("german_expression").upsert(batch, on_conflict="tokens").execute()
        inserted += len(batch)
    return inserted


def import_collocations(db, entries: list[dict]) -> int:
    rows = [
        {
            "verb_lemma": e["verb_lemma"],
            "preposition": e["preposition"],
            "pattern": e["pattern"],
            "source": SOURCE,
        }
        for e in entries
    ]
    inserted = 0
    for batch in _chunks(rows):
        db.table("german_collocation").upsert(
            batch, on_conflict="verb_lemma,preposition"
        ).execute()
        inserted += len(batch)
    return inserted


def main() -> int:
    if not SEED_PATH.exists():
        log.error("Missing %s — regenerate from earlier export.", SEED_PATH)
        return 2

    with SEED_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    db = get_db()

    log.info("Importing %d NVV entries…", len(data.get("nvv", [])))
    nvv_count = import_nvv(db, data.get("nvv", []))
    log.info("  → %d rows", nvv_count)

    log.info("Importing %d fixed expressions…", len(data.get("expression", [])))
    expr_count = import_expressions(db, data.get("expression", []))
    log.info("  → %d rows", expr_count)

    log.info("Importing %d verb+prep collocations…", len(data.get("collocation", [])))
    coll_count = import_collocations(db, data.get("collocation", []))
    log.info("  → %d rows", coll_count)

    log.info("Done. Total: %d rows.", nvv_count + expr_count + coll_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
