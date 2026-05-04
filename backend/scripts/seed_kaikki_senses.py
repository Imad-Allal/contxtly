"""Seed german_sense from Kaikki/Wiktionary.

Every Wiktionary entry has a `senses` array — each sense is one distinct
meaning of the word, with a stable id, glosses, examples, and tags
(register / morphology hints). This is the foundation for WSD: before
translating an ambiguous word, the runtime picks which sense applies,
then translates against the chosen gloss.

Reuses the Kaikki dump from the other Kaikki seeders.

Run:
    cd backend
    python -m scripts.seed_kaikki_senses --dry-run
    python -m scripts.seed_kaikki_senses
"""

import argparse
import json
import logging
import re
import sys
import time
from collections import defaultdict
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

# Glosses matching this regex are morphological pointers to a lemma
# ("inflection of X", "singular imperative of springen", "comparative of
# schön") — they're real Wiktionary entries but redundant for WSD because
# the actual meaning lives on the lemma row. Filtered to keep DB size
# under control.
INFLECTION_GLOSS_RE = re.compile(
    r"^(inflection|form|singular|plural|past participle|present participle|"
    r"past tense|comparative|superlative|feminine|masculine|neuter|"
    r"nominative|accusative|dative|genitive|imperative|subjunctive|"
    r"alternative form|alternative spelling|obsolete form|archaic form|"
    r"dated form|misspelling)( [a-zA-Z]+)*( of )",
    re.IGNORECASE,
)


POS_NORMALISE = {
    "noun": "NOUN", "name": "PROPN", "proper noun": "PROPN",
    "verb": "VERB", "adj": "ADJ", "adjective": "ADJ",
    "adv": "ADV", "adverb": "ADV",
    "phrase": "PHRASE", "proverb": "PHRASE", "idiom": "PHRASE",
    "pron": "PRON", "pronoun": "PRON",
    "prep": "ADP", "preposition": "ADP",
    "conj": "CCONJ", "conjunction": "CCONJ",
    "intj": "INTJ", "interjection": "INTJ",
    "num": "NUM", "numeral": "NUM",
    "particle": "PART",
    "det": "DET", "determiner": "DET",
    "article": "DET",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_KAIKKI)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int, default=0,
                   help="If >0, stop after this many candidate rows (testing)")
    p.add_argument("--include-pos", default="",
                   help="Comma-separated PoS to include (default: all)")
    return p.parse_args()


def extract_examples(sense: dict) -> list[str]:
    """Wiktionary examples can be strings or dicts with a 'text' key."""
    out: list[str] = []
    for ex in sense.get("examples") or []:
        if isinstance(ex, str):
            text = ex.strip()
        elif isinstance(ex, dict):
            text = (ex.get("text") or "").strip()
        else:
            continue
        if text:
            out.append(text)
    return out


def extract_tags(sense: dict) -> list[str]:
    raw = sense.get("tags") or []
    return [str(t).strip() for t in raw if t]


def extract_rows_from_entry(entry: dict, include_pos: set[str] | None) -> list[dict]:
    lemma = entry.get("word")
    if not lemma:
        return []

    pos_raw = (entry.get("pos") or "").lower()
    pos = POS_NORMALISE.get(pos_raw)
    if include_pos and pos not in include_pos:
        return []

    rows: list[dict] = []
    for sense in entry.get("senses") or []:
        sense_id = sense.get("id")
        if not sense_id:
            continue  # without a stable id we can't dedupe across re-runs

        glosses = [g.strip() for g in (sense.get("glosses") or []) if g and g.strip()]
        if not glosses:
            continue

        # Skip morphological "form-of" pointers — see INFLECTION_GLOSS_RE
        if INFLECTION_GLOSS_RE.match(glosses[0]):
            continue

        rows.append({
            "lemma": lemma,
            "pos": pos,
            "sense_id": sense_id,
            "gloss": glosses[0],
            "gloss_extra": glosses[1:] or None,
            "examples": extract_examples(sense) or None,
            "tags": extract_tags(sense) or None,
            "source": SOURCE,
        })
    return rows


def build_rows(input_path: Path, include_pos: set[str] | None, hard_max: int = 0) -> list[dict]:
    rows: list[dict] = []
    counts_per_pos: dict[str, int] = defaultdict(int)
    skipped_foreign = 0
    skipped_no_id = 0
    seen_lines = 0

    with input_path.open(encoding="utf-8") as f:
        for line in f:
            seen_lines += 1
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            lang_code = (entry.get("lang_code") or "").lower()
            if lang_code and lang_code != "de":
                skipped_foreign += 1
                continue

            entry_rows = extract_rows_from_entry(entry, include_pos)
            for r in entry_rows:
                counts_per_pos[r["pos"] or "?"] += 1
            rows.extend(entry_rows)

            if hard_max and len(rows) >= hard_max:
                break

    log.info(
        "Scanned %d entries (skipped %d non-German); extracted %d senses",
        seen_lines, skipped_foreign, len(rows),
    )
    if skipped_no_id:
        log.info("Skipped %d senses without stable ids", skipped_no_id)
    for pos, n in sorted(counts_per_pos.items(), key=lambda kv: -kv[1]):
        log.info("  %s: %d", pos, n)
    return rows


def insert_rows(rows: list[dict]) -> int:
    from db import get_db
    db = get_db()
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        for attempt in range(5):
            try:
                db.table("german_sense").upsert(
                    batch,
                    on_conflict="lemma,pos,sense_id",
                    ignore_duplicates=True,
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
    include_pos: set[str] | None = None
    if args.include_pos.strip():
        include_pos = {p.strip().upper() for p in args.include_pos.split(",") if p.strip()}

    if not args.input.exists():
        log.error(
            "Missing %s. Download from https://kaikki.org/dictionary/German/ first.",
            args.input,
        )
        return 2

    rows = build_rows(args.input, include_pos, hard_max=args.max)

    if args.dry_run:
        log.info("DRY-RUN — sample senses (one per lemma where multiple exist):")
        seen_lemmas: set[str] = set()
        sampled = 0
        for r in rows:
            if r["lemma"] in seen_lemmas:
                continue
            # Show only lemmas with 2+ senses to make the sample interesting
            n_senses = sum(1 for x in rows if x["lemma"] == r["lemma"])
            if n_senses < 2:
                continue
            seen_lemmas.add(r["lemma"])
            log.info("  %s (%s) [%d senses]: %s",
                     r["lemma"], r["pos"] or "?", n_senses, r["gloss"][:90])
            sampled += 1
            if sampled >= 15:
                break
        log.info("Total: %d rows would be upserted.", len(rows))
        return 0

    n = insert_rows(rows)
    log.info("Done. %d rows upserted into german_sense.", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
