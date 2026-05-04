"""Seed german_frequency from HermitDave FrequencyWords (top 50k from OpenSubtitles 2018).

Format of the source file (one entry per line, space-separated):

    ich 5890279
    sie 3806767
    das 3122198
    …

Lines are pre-sorted by descending frequency, so rank = line number.

Download once:
    cd backend/scripts/seed_data
    wget https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/de/de_50k.txt

Run:
    cd backend
    python -m scripts.seed_frequency --dry-run
    python -m scripts.seed_frequency

License: CC-BY-SA 4.0 (HermitDave FrequencyWords / OpenSubtitles 2018).
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
DEFAULT_INPUT = DEFAULT_DATA_DIR / "de_50k.txt"
SOURCE = "opensubtitles_2018"
BATCH = 1000

# Bucket boundaries by rank — coarse "how common" labels for the
# response layer. A = ultra-common (top 1000), B = very common
# (top 5k), C = common (top 20k), D = uncommon-but-attested (top 50k),
# E = rare/oov (anything beyond, not stored).
def bucket_for(rank: int) -> str:
    if rank <= 1000:
        return "A"
    if rank <= 5000:
        return "B"
    if rank <= 20000:
        return "C"
    return "D"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def parse_file(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            word = parts[0]
            try:
                count = int(parts[1])
            except ValueError:
                continue
            rows.append({
                "word": word,
                "rank": line_idx,
                "count": count,
                "bucket": bucket_for(line_idx),
                "source": SOURCE,
            })
    log.info("Parsed %d frequency rows from %s", len(rows), path.name)
    return rows


def insert_rows(rows: list[dict]) -> int:
    from db import get_db
    db = get_db()
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        for attempt in range(5):
            try:
                db.table("german_frequency").upsert(
                    batch,
                    on_conflict="word",
                    ignore_duplicates=False,
                ).execute()
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
        if inserted % 10000 == 0:
            log.info("  …%d inserted", inserted)
    return inserted


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        log.error(
            "Missing %s. Download:\n  wget https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/de/de_50k.txt",
            args.input,
        )
        return 2

    rows = parse_file(args.input)

    if args.dry_run:
        log.info("DRY-RUN — sample of extracted rows:")
        for r in rows[:10]:
            log.info("  rank %5d  bucket %s  count %10d  %s",
                     r["rank"], r["bucket"], r["count"], r["word"])
        # And a sample from the middle/end so the buckets are visible
        if len(rows) > 10000:
            log.info("  …")
            for r in rows[10000:10003]:
                log.info("  rank %5d  bucket %s  count %10d  %s",
                         r["rank"], r["bucket"], r["count"], r["word"])
        if len(rows) > 40000:
            log.info("  …")
            for r in rows[40000:40003]:
                log.info("  rank %5d  bucket %s  count %10d  %s",
                         r["rank"], r["bucket"], r["count"], r["word"])
        log.info("Total: %d rows would be upserted.", len(rows))
        return 0

    n = insert_rows(rows)
    log.info("Done. %d rows upserted into german_frequency.", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
