"""Seed german_translation from Kaikki/Wiktionary.

Wiktionary has translations for hundreds of thousands of German entries
into 50+ languages, written by humans. We pre-load the 10 target
languages the extension exposes so unambiguous word lookups can be
answered from the DB without an LLM call.

Skips:
  - non-German entries (Kaikki German dump includes pages for foreign
    words too — same filter as the idiom seeder)
  - target languages outside the extension's set
  - empty translations
  - obviously-formula entries (translations that are just punctuation
    or a single character)

Reuses the Kaikki dump from seed_kaikki_idioms.py — no new download.

Run:
    cd backend
    python -m scripts.seed_kaikki_translations --dry-run
    python -m scripts.seed_kaikki_translations
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

# Target languages the extension exposes (mirrors LANGUAGES in
# extension/src/app/constants.ts; German is the source so it isn't a target).
TARGET_LANGS = {"en", "es", "fr", "it", "pt", "zh", "ja", "ko", "ar", "ru"}

# Map Kaikki's language codes (often 2-letter, sometimes 3) to our 2-letter set.
LANG_NORMALISE = {
    "en": "en", "eng": "en",
    "es": "es", "spa": "es",
    "fr": "fr", "fra": "fr",
    "it": "it", "ita": "it",
    "pt": "pt", "por": "pt",
    "zh": "zh", "cmn": "zh", "zho": "zh",
    "ja": "ja", "jpn": "ja",
    "ko": "ko", "kor": "ko",
    "ar": "ar", "ara": "ar",
    "ru": "ru", "rus": "ru",
}

# Map Wiktionary PoS strings to our short tags.
POS_NORMALISE = {
    "noun": "NOUN", "name": "PROPN", "proper noun": "PROPN",
    "verb": "VERB", "adj": "ADJ", "adjective": "ADJ",
    "adv": "ADV", "adverb": "ADV",
    "phrase": "PHRASE", "proverb": "PHRASE", "idiom": "PHRASE",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_KAIKKI)
    p.add_argument("--target-langs", default=",".join(sorted(TARGET_LANGS)),
                   help="Comma-separated 2-letter target langs to keep")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int, default=0,
                   help="If >0, stop after this many candidate rows (testing)")
    return p.parse_args()


def normalise_translation(text: str) -> str | None:
    """Strip whitespace and reject obvious junk."""
    if not text:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    # Filter out single-character "translations" that are usually
    # punctuation or stray characters from the parser
    if len(cleaned) == 1 and not cleaned.isalpha():
        return None
    return cleaned


def extract_rows_from_entry(entry: dict, wanted_langs: set[str]) -> list[dict]:
    """Return one row per (lemma, pos, sense_id, target_lang, translation) found in entry."""
    lemma = entry.get("word")
    if not lemma:
        return []

    pos_raw = (entry.get("pos") or "").lower()
    pos = POS_NORMALISE.get(pos_raw)

    rows: list[dict] = []
    seen: set[tuple] = set()  # dedupe within this entry

    def add(target_lang: str, translation: str, sense_id: str | None) -> None:
        key = (lemma, pos, sense_id, target_lang, translation)
        if key in seen:
            return
        seen.add(key)
        rows.append({
            "lemma": lemma,
            "pos": pos,
            "sense_id": sense_id,
            "target_lang": target_lang,
            "translation": translation,
            "source": SOURCE,
        })

    # Translations attached to specific senses
    for sense in entry.get("senses", []) or []:
        for trans in sense.get("translations") or []:
            code_raw = (trans.get("code") or trans.get("lang_code") or "").lower()
            target_lang = LANG_NORMALISE.get(code_raw)
            if target_lang not in wanted_langs:
                continue
            translation = normalise_translation(trans.get("word") or "")
            if not translation:
                continue
            add(target_lang, translation, None)  # sense_id stays NULL until step 2

    # Top-level translations (Kaikki sometimes hoists them)
    for trans in entry.get("translations") or []:
        code_raw = (trans.get("code") or trans.get("lang_code") or "").lower()
        target_lang = LANG_NORMALISE.get(code_raw)
        if target_lang not in wanted_langs:
            continue
        translation = normalise_translation(trans.get("word") or "")
        if not translation:
            continue
        add(target_lang, translation, None)

    return rows


def build_rows(input_path: Path, wanted_langs: set[str], hard_max: int = 0) -> list[dict]:
    rows: list[dict] = []
    counts_per_lang: dict[str, int] = defaultdict(int)
    skipped_foreign = 0
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

            # German-only — Kaikki German dump includes foreign-language pages
            lang_code = (entry.get("lang_code") or "").lower()
            if lang_code and lang_code != "de":
                skipped_foreign += 1
                continue

            entry_rows = extract_rows_from_entry(entry, wanted_langs)
            for r in entry_rows:
                counts_per_lang[r["target_lang"]] += 1
            rows.extend(entry_rows)

            if hard_max and len(rows) >= hard_max:
                break

    log.info(
        "Scanned %d entries (skipped %d non-German); extracted %d translation rows",
        seen_lines, skipped_foreign, len(rows),
    )
    for lang, n in sorted(counts_per_lang.items()):
        log.info("  %s: %d", lang, n)
    return rows


def insert_rows(rows: list[dict]) -> int:
    """Upsert with retry on transient network errors."""
    from db import get_db
    db = get_db()
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        for attempt in range(5):
            try:
                db.table("german_translation").upsert(
                    batch,
                    on_conflict="lemma,pos,sense_id,target_lang,translation",
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
    wanted = {t.strip() for t in args.target_langs.split(",") if t.strip()}
    unknown = wanted - TARGET_LANGS
    if unknown:
        log.warning("Ignoring unknown target langs: %s", unknown)
        wanted &= TARGET_LANGS
    if not wanted:
        log.error("No valid target langs specified")
        return 2

    if not args.input.exists():
        log.error(
            "Missing %s. Download from https://kaikki.org/dictionary/German/ first.",
            args.input,
        )
        return 2

    rows = build_rows(args.input, wanted, hard_max=args.max)

    if args.dry_run:
        log.info("DRY-RUN — sample of extracted rows:")
        # Show a few rows per language to make the sample useful
        per_lang_samples: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            if len(per_lang_samples[r["target_lang"]]) < 3:
                per_lang_samples[r["target_lang"]].append(r)
        for lang in sorted(per_lang_samples):
            for r in per_lang_samples[lang]:
                log.info("  [%s] %s (%s) ⇒ %s",
                         lang, r["lemma"], r["pos"] or "?", r["translation"])
        log.info("Total: %d rows would be upserted.", len(rows))
        return 0

    n = insert_rows(rows)
    log.info("Done. %d rows upserted into german_translation.", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
