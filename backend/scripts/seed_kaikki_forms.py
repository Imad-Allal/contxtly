"""Seed german_verb_form + german_noun from Kaikki/Wiktionary.

One pass over the German JSONL extracts both:
  - inflected verb forms with their morphology tags
  - noun gender + plural

Reuses the Kaikki dump from the other Kaikki seeders.

Run:
    cd backend
    python -m scripts.seed_kaikki_forms --dry-run
    python -m scripts.seed_kaikki_forms

Notes on filtering:
  - Verb form rows: skipped if `tags` only contains metadata
    (table-tags, inflection-template, class, auxiliary) — those rows
    in the Kaikki dump describe conjugation tables, not real forms
  - Noun rows: gender parsed from head_templates[0].args['1'] (Kaikki
    encodes gender as the first letter of the template arg). A noun
    with multiple genders gets multiple rows (Band f / Band n / …)
"""

import argparse
import json
import logging
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

# Tags that mark a Kaikki "form" entry as table metadata, not an
# actual inflected word. Skip these.
META_FORM_TAGS = {
    "table-tags",
    "inflection-template",
    "class",
    "auxiliary",
}

# Tags that, if present, mark a real morphological form worth keeping.
REAL_FORM_TAGS = {
    "first-person", "second-person", "third-person",
    "singular", "plural",
    "present", "past", "preterite", "future",
    "indicative", "subjunctive", "imperative",
    "participle", "infinitive",
    "active", "passive",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_KAIKKI)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int, default=0,
                   help="If >0, stop after this many candidate rows (testing)")
    p.add_argument("--include", default="verb,noun",
                   choices=["verb", "noun", "verb,noun"],
                   help="Which kinds to extract")
    return p.parse_args()


def is_real_form(tags: list[str]) -> bool:
    if not tags:
        return False
    tag_set = set(tags)
    if tag_set & META_FORM_TAGS:
        return False
    return bool(tag_set & REAL_FORM_TAGS)


def extract_verb_forms(entry: dict) -> list[dict]:
    lemma = entry.get("word")
    if not lemma:
        return []
    rows: list[dict] = []
    seen: set[tuple] = set()
    for f in entry.get("forms") or []:
        surface = (f.get("form") or "").strip()
        if not surface or surface == lemma:
            continue
        tags = [str(t).strip() for t in (f.get("tags") or []) if t]
        if not is_real_form(tags):
            continue
        key = (surface, tuple(tags))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "surface": surface,
            "lemma": lemma,
            "tags": tags,
            "source": SOURCE,
        })
    return rows


def extract_noun(entry: dict) -> list[dict]:
    lemma = entry.get("word")
    if not lemma:
        return []

    # Gender lives in head_templates[0].args['1'], encoded as e.g.
    # 'm,es:s,e:^e' — take the first letter of the comma-separated
    # head, which is m/f/n. Some entries have multiple genders
    # separated by commas at the top level (e.g. 'm,n' for Band).
    head_templates = entry.get("head_templates") or []
    if not head_templates:
        return []
    args = (head_templates[0] or {}).get("args") or {}
    raw = (args.get("1") or "").strip()
    if not raw:
        return []
    # The arg before the first ":" or "," contains the gender(s)
    head = raw.split(":")[0]
    genders: list[str] = []
    for token in head.split(","):
        token = token.strip()
        if token in ("m", "f", "n"):
            genders.append(token)
    if not genders:
        return []

    # Plural: pick the first form tagged 'plural' that isn't tagged
    # 'error-unknown-tag' (Kaikki marks dubious entries that way).
    plural = None
    for f in entry.get("forms") or []:
        tags = set(f.get("tags") or [])
        if "plural" in tags and "error-unknown-tag" not in tags:
            plural = (f.get("form") or "").strip() or None
            if plural:
                break

    return [
        {"lemma": lemma, "gender": g, "plural": plural, "source": SOURCE}
        for g in genders
    ]


def build(input_path: Path, include: set[str], hard_max: int = 0) -> tuple[list[dict], list[dict]]:
    verb_rows: list[dict] = []
    noun_rows: list[dict] = []
    seen_noun: set[tuple] = set()
    seen_lines = 0
    skipped_foreign = 0

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

            pos = (entry.get("pos") or "").lower()
            if pos == "verb" and "verb" in include:
                verb_rows.extend(extract_verb_forms(entry))
            elif pos == "noun" and "noun" in include:
                for r in extract_noun(entry):
                    key = (r["lemma"], r["gender"])
                    if key in seen_noun:
                        continue
                    seen_noun.add(key)
                    noun_rows.append(r)

            if hard_max and len(verb_rows) + len(noun_rows) >= hard_max:
                break

    log.info(
        "Scanned %d entries (%d non-German skipped); %d verb forms, %d nouns",
        seen_lines, skipped_foreign, len(verb_rows), len(noun_rows),
    )
    return verb_rows, noun_rows


def insert_batch(table: str, rows: list[dict], on_conflict: str | None = None) -> int:
    from db import get_db
    db = get_db()
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        for attempt in range(5):
            try:
                builder = db.table(table)
                if on_conflict:
                    builder.upsert(
                        batch, on_conflict=on_conflict, ignore_duplicates=True,
                    ).execute()
                else:
                    builder.insert(batch).execute()
                break
            except Exception as e:
                if attempt == 4:
                    log.error("[%s] batch %d failed after 5 retries: %s",
                              table, i // BATCH, e)
                    raise
                wait = 2 ** attempt
                log.warning(
                    "[%s] batch %d attempt %d failed (%s) — retrying in %ds",
                    table, i // BATCH, attempt + 1, type(e).__name__, wait,
                )
                time.sleep(wait)
        inserted += len(batch)
        if inserted % 10000 == 0:
            log.info("  [%s] …%d inserted", table, inserted)
    return inserted


def main() -> int:
    args = parse_args()
    include = set(args.include.split(","))

    if not args.input.exists():
        log.error(
            "Missing %s. Download from https://kaikki.org/dictionary/German/ first.",
            args.input,
        )
        return 2

    verb_rows, noun_rows = build(args.input, include, hard_max=args.max)

    if args.dry_run:
        log.info("DRY-RUN — sample verb forms (10):")
        for r in verb_rows[:10]:
            log.info("  %s ← %s   %s",
                     r["surface"], r["lemma"], ",".join(r["tags"]))
        log.info("DRY-RUN — sample nouns (10):")
        # Pick rows with non-null plurals so the sample is informative
        sampled = [r for r in noun_rows if r["plural"]][:10]
        for r in sampled:
            log.info("  %s (%s, plural %s)", r["lemma"], r["gender"], r["plural"])
        log.info("Totals: %d verb forms, %d nouns would be upserted.",
                 len(verb_rows), len(noun_rows))
        return 0

    if verb_rows:
        n = insert_batch("german_verb_form", verb_rows)  # no upsert; small enough to truncate-and-insert
        log.info("Done. %d verb forms inserted.", n)
    if noun_rows:
        n = insert_batch("german_noun", noun_rows, on_conflict="lemma,gender")
        log.info("Done. %d nouns upserted.", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
