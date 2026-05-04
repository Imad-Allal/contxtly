"""Seed german_expression with idioms (Redewendungen) from Kaikki/Wiktionary.

Kaikki.org publishes pre-parsed Wiktionary as JSONL. We pull the German
edition's "phrase" / "idiom" entries and insert them as figurative
fixed expressions.

Download once:
    cd backend/scripts/seed_data
    wget https://kaikki.org/dictionary/German/kaikki.org-dictionary-German.jsonl
    # ~hundreds of MB. License: CC BY-SA 4.0 (Wiktionary)

Then run:
    cd backend
    python -m scripts.seed_kaikki_idioms --dry-run
    python -m scripts.seed_kaikki_idioms

What we keep:
  - Multi-word headwords (≥ 2 tokens after a basic split)
  - Entries whose pos is "phrase" / "proverb" OR senses tagged
    "idiomatic" / "figurative"
  - Glosses become meaning_de / meaning_targets

We tag every row source='kaikki_wiktionary' and figurative=true so we
can roll back / re-attribute. Per the CC BY-SA 4.0 license, the deployed
service must credit Wiktionary; the source column makes that auditable.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path(__file__).parent / "seed_data"
DEFAULT_KAIKKI = DEFAULT_DATA_DIR / "kaikki.org-dictionary-German.jsonl"
SOURCE = "kaikki_wiktionary"
BATCH = 500

# Kaikki PoS tags or sense tags that mark something as a fixed/figurative phrase
PHRASE_POS = {"phrase", "proverb", "idiom"}
PHRASE_SENSE_TAGS = {"idiomatic", "figurative", "set phrase", "proverbial"}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_KAIKKI,
                   help="Path to Kaikki German JSONL dump")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int, default=0,
                   help="If >0, stop after extracting this many candidate rows")
    return p.parse_args()


def is_phrase_entry(entry: dict) -> bool:
    """Decide whether this Kaikki entry should be treated as a figurative expression."""
    pos = (entry.get("pos") or "").lower()
    if pos in PHRASE_POS:
        return True

    # Multi-word headword + at least one sense flagged as idiomatic/figurative
    word = entry.get("word", "")
    if len(word.split()) < 2:
        return False
    for sense in entry.get("senses", []):
        tags = {t.lower() for t in sense.get("tags", [])}
        if tags & PHRASE_SENSE_TAGS:
            return True
    return False


def tokenise(headword: str) -> list[str]:
    """Naive whitespace split — Kaikki headwords use simple space separation."""
    return [t for t in headword.split() if t]


def first_gloss(entry: dict) -> str | None:
    for sense in entry.get("senses", []):
        glosses = sense.get("glosses") or sense.get("raw_glosses") or []
        if glosses:
            return glosses[0]
    return None


def extract_translations(entry: dict) -> dict[str, str]:
    """Return {lang_2letter: first_translation_text} from any sense."""
    out: dict[str, str] = {}
    for sense in entry.get("senses", []):
        for trans in sense.get("translations") or []:
            code = trans.get("code") or trans.get("lang_code")
            text = trans.get("word")
            if not code or not text or code in out:
                continue
            # Kaikki uses 2-letter codes for major languages
            if len(code) == 2:
                out[code] = text
    return out


def build_rows(input_path: Path, hard_max: int = 0) -> list[dict]:
    rows: list[dict] = []
    seen_tokens: set[tuple[str, ...]] = set()
    skipped_short = skipped_no_gloss = 0

    with input_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Skip non-German entries — the German Wiktionary dump
            # includes pages describing foreign-language words too.
            lang_code = (entry.get("lang_code") or "").lower()
            if lang_code and lang_code != "de":
                continue

            if not is_phrase_entry(entry):
                continue

            tokens = tokenise(entry.get("word", ""))
            if len(tokens) < 2:
                skipped_short += 1
                continue

            key = tuple(tokens)
            if key in seen_tokens:
                continue
            seen_tokens.add(key)

            gloss = first_gloss(entry)
            if not gloss:
                skipped_no_gloss += 1
                continue

            translations = extract_translations(entry)

            rows.append({
                "tokens": list(tokens),
                "canonical": " ".join(tokens),
                "figurative": True,
                "meaning_de": gloss,
                "meaning_targets": translations or None,
                "source": SOURCE,
            })

            if hard_max and len(rows) >= hard_max:
                break

    log.info(
        "Extracted %d idioms (skipped %d single-word, %d gloss-less)",
        len(rows), skipped_short, skipped_no_gloss,
    )
    return rows


def insert_rows(rows: list[dict]) -> int:
    from db import get_db
    db = get_db()
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        db.table("german_expression").upsert(
            batch, on_conflict="tokens", ignore_duplicates=True,
        ).execute()
        inserted += len(batch)
        if inserted % 2000 == 0:
            log.info("  …%d upserted", inserted)
    return inserted


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        log.error(
            "Missing %s. Download from https://kaikki.org/dictionary/German/ first.",
            args.input,
        )
        return 2

    rows = build_rows(args.input, hard_max=args.max)

    if args.dry_run:
        log.info("DRY-RUN — sample of extracted rows:")
        for r in rows[:10]:
            log.info("  %s   ⇒   %s", r["canonical"], (r["meaning_de"] or "")[:80])
        log.info("Total: %d rows would be upserted.", len(rows))
        return 0

    n = insert_rows(rows)
    log.info("Done. %d rows upserted into german_expression.", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
