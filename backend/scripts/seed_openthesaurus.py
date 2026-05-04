"""Seed german_synonym_group from OpenThesaurus.

OpenThesaurus is a free, crowd-sourced German thesaurus. Each line in
the text dump is one synonym group; words within a group are
separated by ';'. Lines starting with '#' are comments.

Download once:
    cd backend/scripts/seed_data
    wget https://www.openthesaurus.de/export/OpenThesaurus-Textversion.zip
    unzip OpenThesaurus-Textversion.zip
    # The archive contains a single .txt file (filename varies by date,
    # something like 'openthesaurus.txt')

Run:
    cd backend
    python -m scripts.seed_openthesaurus --dry-run
    python -m scripts.seed_openthesaurus

License: CC BY-SA 4.0 / LGPL. Surface "OpenThesaurus.de" attribution
in the UI when this data is shown to the user.
"""

import argparse
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path(__file__).parent / "seed_data"
SOURCE = "openthesaurus"
BATCH = 500


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input", type=Path, default=None,
        help="Path to the unzipped OpenThesaurus .txt file. "
             "Auto-detected from seed_data/ if not given.",
    )
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def find_input() -> Path | None:
    """OpenThesaurus filename varies by date — find any .txt that looks like it."""
    for candidate in sorted(DEFAULT_DATA_DIR.glob("*.txt")):
        # Look for a file whose first non-comment line has multiple ';'
        # — strong signal it's an OpenThesaurus dump.
        try:
            with candidate.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.count(";") >= 1:
                        return candidate
                    break
        except (OSError, UnicodeDecodeError):
            continue
    return None


def parse_groups(path: Path) -> list[list[str]]:
    """Read OpenThesaurus text dump → list of synonym groups."""
    groups: list[list[str]] = []
    skipped_singletons = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            members = [m.strip() for m in line.split(";")]
            members = [m for m in members if m]  # drop empties
            # Drop trailing parenthetical disambiguators on each member,
            # e.g. "Bank (Sitzgelegenheit)" → "Bank". Keep the bare word.
            members = [m.split(" (")[0].strip() for m in members]
            members = [m for m in members if m]
            if len(members) < 2:
                skipped_singletons += 1
                continue
            # De-dupe within group (same word with different parentheticals)
            seen = set()
            deduped: list[str] = []
            for m in members:
                if m not in seen:
                    seen.add(m)
                    deduped.append(m)
            if len(deduped) < 2:
                skipped_singletons += 1
                continue
            groups.append(deduped)
    log.info(
        "Parsed %d synonym groups (skipped %d singletons after dedupe)",
        len(groups), skipped_singletons,
    )
    return groups


def insert_groups(groups: list[list[str]]) -> int:
    from db import get_db
    db = get_db()
    rows = [{"members": g, "source": SOURCE} for g in groups]
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        for attempt in range(5):
            try:
                # No natural unique key on synonym groups (order-sensitive,
                # crowd-sourced overlaps), so just plain inserts. Run is
                # one-shot — to re-import, TRUNCATE first.
                db.table("german_synonym_group").insert(batch).execute()
                break
            except Exception as e:
                if attempt == 4:
                    log.error("Batch %d failed after 5 retries: %s", i // BATCH, e)
                    raise
                wait = 2 ** attempt
                log.warning(
                    "Batch %d attempt %d failed (%s) — retrying in %ds",
                    i // BATCH, attempt + 1, type(e).__name__, wait,
                )
                time.sleep(wait)
        inserted += len(batch)
        if inserted % 5000 == 0:
            log.info("  …%d inserted", inserted)
    return inserted


def main() -> int:
    args = parse_args()

    input_path = args.input or find_input()
    if not input_path or not input_path.exists():
        log.error(
            "No OpenThesaurus dump found in %s. Download:\n"
            "  cd backend/scripts/seed_data\n"
            "  wget https://www.openthesaurus.de/export/OpenThesaurus-Textversion.zip\n"
            "  unzip OpenThesaurus-Textversion.zip",
            DEFAULT_DATA_DIR,
        )
        return 2

    log.info("Reading %s", input_path)
    groups = parse_groups(input_path)

    if args.dry_run:
        log.info("DRY-RUN — sample of extracted groups:")
        for g in groups[:10]:
            log.info("  %s", ", ".join(g[:8]) + (" …" if len(g) > 8 else ""))
        log.info("Total: %d groups would be inserted.", len(groups))
        return 0

    n = insert_groups(groups)
    log.info("Done. %d groups inserted into german_synonym_group.", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
