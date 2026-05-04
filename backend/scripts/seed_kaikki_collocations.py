"""Seed german_collocation with verb+preposition patterns from Kaikki.

Strategy is conservative — Wiktionary data is heterogeneous and a noisy
import would pollute detection. We only keep a row when the preposition
is unambiguously attached to the verb's argument structure.

Two signals we trust:

  1. Sense glosses or raw_glosses that include a literal "+ <prep>" or
     "(with <prep>)" hint. Wiktionary regularly writes things like
     "to think about something (+ acc.)" and "[with über]".

  2. The 'related' / 'derived' / 'examples' fields where a German
     example sentence makes the verb+prep pattern visible. We extract
     "<verb_form> ... <prep>" within a short window.

Anything that doesn't trip one of these signals is skipped. Better to
under-import than to introduce wrong collocations.

Download once:
    cd backend/scripts/seed_data
    wget https://kaikki.org/dictionary/German/kaikki.org-dictionary-German.jsonl

Run:
    cd backend
    python -m scripts.seed_kaikki_collocations --dry-run
    python -m scripts.seed_kaikki_collocations
"""

import argparse
import json
import logging
import re
import sys
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

# All German prepositions we will accept as a collocation tail.
# Restricting the set is the cheapest way to stop random adverbs from
# being mistaken for prepositions.
GERMAN_PREPS = {
    "an", "auf", "aus", "bei", "durch", "für", "gegen", "in", "mit",
    "nach", "über", "um", "unter", "von", "vor", "zu", "zwischen",
    "wegen", "trotz", "während", "ohne",
}

GLOSS_PREP_PATTERNS = [
    re.compile(r"\(\s*\+\s*(?P<prep>[A-Za-zäöüÄÖÜß]+)\s*[\.,)]", re.I),
    re.compile(r"\bwith\s+(?P<prep>[A-Za-zäöüÄÖÜß]+)\b", re.I),
    re.compile(r"\[\s*with\s+(?P<prep>[A-Za-zäöüÄÖÜß]+)\s*\]", re.I),
    re.compile(r"\b(?P<prep>[A-Za-zäöüÄÖÜß]+)\s*\+\s*(?:dat|acc|gen)\b", re.I),
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_KAIKKI)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int, default=0)
    return p.parse_args()


def extract_prep_from_gloss(text: str) -> str | None:
    for pat in GLOSS_PREP_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        prep = m.group("prep").lower()
        if prep in GERMAN_PREPS:
            return prep
    return None


def extract_prep_from_examples(verb: str, examples: list[dict]) -> str | None:
    """Look for verb form + preposition within a short window in any example."""
    verb_root = verb.lower()
    for ex in examples or []:
        text = (ex.get("text") or "").lower()
        if not text:
            continue
        # Find the verb's surface form (rough — accept any word starting with
        # the first 4 chars of the lemma) and check the next ~8 tokens.
        words = re.findall(r"[a-zäöüß]+", text)
        for i, w in enumerate(words):
            if not w.startswith(verb_root[:4]):
                continue
            for nxt in words[i + 1 : i + 8]:
                if nxt in GERMAN_PREPS:
                    return nxt
    return None


def build_rows(input_path: Path, hard_max: int = 0) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    rows: list[dict] = []
    counts = defaultdict(int)

    with input_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Skip non-German entries (the German Wiktionary dump
            # includes pages for foreign-language words).
            lang_code = (entry.get("lang_code") or "").lower()
            if lang_code and lang_code != "de":
                continue

            if (entry.get("pos") or "").lower() != "verb":
                continue

            verb = entry.get("word") or ""
            if not verb or " " in verb:
                continue
            verb_lemma = verb.lower()

            # Try gloss-based extraction first
            for sense in entry.get("senses", []):
                glosses = sense.get("glosses") or sense.get("raw_glosses") or []
                gloss_text = " ".join(glosses)
                prep = extract_prep_from_gloss(gloss_text)
                if not prep:
                    prep = extract_prep_from_examples(verb_lemma, sense.get("examples"))
                if not prep:
                    continue

                key = (verb_lemma, prep)
                if key in seen:
                    continue
                seen.add(key)
                counts["gloss" if extract_prep_from_gloss(gloss_text) else "examples"] += 1

                rows.append({
                    "verb_lemma": verb_lemma,
                    "preposition": prep,
                    "pattern": f"{verb_lemma} + {prep}",
                    "source": SOURCE,
                })

                if hard_max and len(rows) >= hard_max:
                    break
            if hard_max and len(rows) >= hard_max:
                break

    log.info(
        "Extracted %d collocations (gloss=%d, examples=%d)",
        len(rows), counts["gloss"], counts["examples"],
    )
    return rows


def insert_rows(rows: list[dict]) -> int:
    from db import get_db
    db = get_db()
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        db.table("german_collocation").upsert(
            batch, on_conflict="verb_lemma,preposition", ignore_duplicates=True,
        ).execute()
        inserted += len(batch)
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
        for r in rows[:15]:
            log.info("  %s + %s   ⇒   %s",
                     r["verb_lemma"], r["preposition"], r["pattern"])
        log.info("Total: %d rows would be upserted.", len(rows))
        return 0

    n = insert_rows(rows)
    log.info("Done. %d rows upserted into german_collocation.", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
