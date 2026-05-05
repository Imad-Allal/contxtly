"""Seed german_bilingual_example from Tatoeba per-language exports.

Tatoeba's per-language directory at
    https://downloads.tatoeba.org/exports/per_language/<iso3>/
contains:
    <iso3>_sentences.tsv.bz2          monolingual sentences (id, lang, text)
    <iso3>-<other>_links.tsv.bz2      DE↔other id-pair links

There is NO pre-aligned bilingual file — we still have to join sentences
on links — but each file is small (low MB) instead of the global GB dump.

Per target language we need three files:
    - deu_sentences.tsv             (downloaded once, used by every pair)
    - <tgt_iso3>_sentences.tsv      (one per target lang)
    - deu-<tgt_iso3>_links.tsv      (one per target lang)

Download (German base + English/French/Spanish targets):
    cd backend/scripts/seed_data
    # German sentences (used by every pair)
    wget https://downloads.tatoeba.org/exports/per_language/deu/deu_sentences.tsv.bz2
    # English target
    wget https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences.tsv.bz2
    wget https://downloads.tatoeba.org/exports/per_language/deu/deu-eng_links.tsv.bz2
    # French target
    wget https://downloads.tatoeba.org/exports/per_language/fra/fra_sentences.tsv.bz2
    wget https://downloads.tatoeba.org/exports/per_language/deu/deu-fra_links.tsv.bz2
    # Spanish target
    wget https://downloads.tatoeba.org/exports/per_language/spa/spa_sentences.tsv.bz2
    wget https://downloads.tatoeba.org/exports/per_language/deu/deu-spa_links.tsv.bz2
    bunzip2 *.bz2

Then run:
    cd backend
    python -m scripts.seed_tatoeba --dry-run                   # preview
    python -m scripts.seed_tatoeba --target-langs en,fr,es     # do it

Pipeline per target language:
    1. Read deu_sentences.tsv into {de_id: de_text}     (one read per run)
    2. Read <tgt>_sentences.tsv into {tgt_id: tgt_text}
    3. Read deu-<tgt>_links.tsv → list of (de_id, tgt_id)
    4. For each link, build a pair; filter by --max-len
    5. Tokenise the German side once with spaCy; emit one row per
       content lemma, capped at --max-per-lemma per (lemma, target_lang)
    6. Bulk-upsert (dedupe on source + external_id + target_lang)

Attribution: Tatoeba is CC BY 2.0 FR. Every row is tagged
source='tatoeba'; surface "from Tatoeba (CC BY 2.0 FR)" in the UI
wherever this data appears.
"""

import argparse
import csv
import hashlib
import json
import logging
import pickle
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
SOURCE = "tatoeba"
BATCH = 500

# 2-letter target lang → Tatoeba ISO 639-3
# Mirrors the LANGUAGES constant in extension/src/app/constants.ts
# (German is the source, so it isn't a target).
# zh → cmn: Tatoeba uses "cmn" for Mandarin Chinese.
ISO2_TO_ISO3 = {
    "en": "eng",
    "es": "spa",
    "fr": "fra",
    "it": "ita",
    "pt": "por",
    "zh": "cmn",
    "ja": "jpn",
    "ko": "kor",
    "ar": "ara",
    "ru": "rus",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                   help="Directory containing the unpacked Tatoeba TSVs")
    p.add_argument("--target-langs", default="en,es,fr,it,pt,zh,ja,ko,ar,ru",
                   help="Comma-separated 2-letter target langs to import "
                        "(default: every target the extension exposes)")
    p.add_argument("--max-len", type=int, default=80,
                   help="Skip German sentences longer than this many characters")
    p.add_argument("--max-per-lemma", type=int, default=5,
                   help="Cap examples kept per (lemma, target_lang) pair")
    p.add_argument("--dry-run", action="store_true",
                   help="Print stats without inserting into Postgres")
    p.add_argument("--rebuild-cache", action="store_true",
                   help="Force re-tokenisation even if a fresh cache exists")
    return p.parse_args()


def _cache_key(args, paths: list[Path]) -> str:
    """Hash of inputs that, if unchanged, means tokenisation can be skipped."""
    parts = {
        "target_langs": sorted(args.target_langs.split(",")),
        "max_len": args.max_len,
        "max_per_lemma": args.max_per_lemma,
        "files": [(p.name, p.stat().st_mtime, p.stat().st_size) for p in paths],
    }
    blob = json.dumps(parts, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _cache_path(data_dir: Path, key: str) -> Path:
    return data_dir / ".cache" / f"tatoeba_rows_{key}.pkl"


def load_cached_rows(data_dir: Path, key: str) -> list[dict] | None:
    path = _cache_path(data_dir, key)
    if not path.exists():
        return None
    try:
        with path.open("rb") as f:
            rows = pickle.load(f)
        log.info("Cache hit: loaded %d rows from %s", len(rows), path.name)
        return rows
    except Exception as e:
        log.warning("Cache read failed (%s) — re-tokenising", e)
        return None


def save_cached_rows(data_dir: Path, key: str, rows: list[dict]) -> None:
    path = _cache_path(data_dir, key)
    path.parent.mkdir(exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(rows, f, protocol=pickle.HIGHEST_PROTOCOL)
    log.info("Cached %d rows to %s", len(rows), path.name)


def load_sentences(path: Path) -> dict[int, str]:
    """Read a Tatoeba per-language sentences TSV.

    File layout: id \\t lang_code \\t text   (3 columns, lang always
    matches the directory). Older dumps can be 2 columns (id, text).
    """
    out: dict[int, str] = {}
    with path.open(encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            if len(row) >= 3:
                sid_str, _, text = row[0], row[1], row[2]
            elif len(row) == 2:
                sid_str, text = row
            else:
                continue
            try:
                sid = int(sid_str)
            except ValueError:
                continue
            if text:
                out[sid] = text
    log.info("Loaded %d sentences from %s", len(out), path.name)
    return out


def load_links(path: Path) -> list[tuple[int, int]]:
    """Read a deu-<other>_links.tsv: source_id \\t translation_id."""
    out: list[tuple[int, int]] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            if len(row) < 2:
                continue
            try:
                a, b = int(row[0]), int(row[1])
            except ValueError:
                continue
            out.append((a, b))
    log.info("Loaded %d links from %s", len(out), path.name)
    return out


def build_pairs_for_lang(
    de_sentences: dict[int, str],
    tgt_sentences: dict[int, str],
    links: list[tuple[int, int]],
    max_len: int,
) -> list[tuple[int, str, int, str]]:
    """Return list of (de_id, de_text, tgt_id, tgt_text)."""
    pairs: list[tuple[int, str, int, str]] = []
    skipped_long = 0
    for a, b in links:
        # Links can go either direction depending on which side is "source"
        if a in de_sentences and b in tgt_sentences:
            de_id, de_text, tgt_id, tgt_text = a, de_sentences[a], b, tgt_sentences[b]
        elif b in de_sentences and a in tgt_sentences:
            de_id, de_text, tgt_id, tgt_text = b, de_sentences[b], a, tgt_sentences[a]
        else:
            continue
        if len(de_text) > max_len:
            skipped_long += 1
            continue
        pairs.append((de_id, de_text, tgt_id, tgt_text))
    log.info("Built %d pairs (skipped %d > %d chars)", len(pairs), skipped_long, max_len)
    return pairs


def index_by_lemma(
    pairs_by_lang: dict[str, list[tuple[int, str, int, str]]],
    max_per_lemma: int,
) -> list[dict]:
    """Tokenise each German sentence once, emit one row per content lemma per target lang."""
    import spacy
    nlp = spacy.load("de_core_news_lg", disable=["ner", "parser"])

    out: list[dict] = []
    counts: dict[tuple[str, str], int] = defaultdict(int)
    keep_pos = {"NOUN", "VERB", "ADJ", "PROPN"}

    # Group pairs by German sentence so we tokenise each only once
    by_de_text: dict[str, dict] = {}
    for target_lang, pairs in pairs_by_lang.items():
        for de_id, de_text, tgt_id, tgt_text in pairs:
            entry = by_de_text.setdefault(de_text, {"de_id": de_id, "targets": []})
            entry["targets"].append({
                "lang": target_lang,
                "tgt_id": tgt_id,
                "text": tgt_text,
            })

    log.info("Tokenising %d unique German sentences", len(by_de_text))
    # Batch through spaCy with nlp.pipe for ~10× speedup vs. per-sentence nlp().
    # as_tuples lets us pass each sentence's metadata alongside and recover it
    # with the parsed Doc — no need to re-key by text afterwards.
    items = list(by_de_text.items())
    processed = 0
    log_every = max(10000, len(items) // 20)
    # nlp.pipe(as_tuples=True) takes (text, context) tuples and yields
    # (doc, context). Each item here is (de_text, info_dict) — spaCy reads
    # the first as text, hands the second back unchanged. We recover de_text
    # from doc.text.
    for doc, info in nlp.pipe(items, as_tuples=True, batch_size=256):
        de_text = doc.text
        seen_lemmas: set[str] = set()
        for tok in doc:
            if tok.pos_ not in keep_pos:
                continue
            lemma = tok.lemma_.lower()
            if not lemma or len(lemma) < 2:
                continue
            if lemma in seen_lemmas:
                continue
            seen_lemmas.add(lemma)

            for target in info["targets"]:
                key = (lemma, target["lang"])
                if counts[key] >= max_per_lemma:
                    continue
                counts[key] += 1
                out.append({
                    "lemma": lemma,
                    "sentence_de": de_text,
                    "sentence_target": target["text"],
                    "target_lang": target["lang"],
                    "source": SOURCE,
                    "external_id": f"{info['de_id']}-{target['tgt_id']}",
                })
        processed += 1
        if processed % log_every == 0:
            log.info("  …tokenised %d/%d sentences", processed, len(items))

    log.info("Indexed %d (lemma × target_lang) example rows", len(out))
    return out


def insert_rows(rows: list[dict]) -> int:
    """Upsert in batches with retry on transient network errors.

    Supabase's HTTP/2 connection occasionally drops mid-stream; retry the
    failing batch a few times with exponential backoff before giving up.
    Already-inserted rows are no-ops thanks to ignore_duplicates=True.
    """
    import time
    from db import get_db
    db = get_db()

    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        for attempt in range(5):
            try:
                db.table("german_bilingual_example").upsert(
                    batch,
                    on_conflict="source,external_id,target_lang,lemma",
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
        if inserted % 5000 == 0:
            log.info("  …%d inserted", inserted)
    return inserted


def main() -> int:
    args = parse_args()
    target_langs = [t.strip() for t in args.target_langs.split(",") if t.strip()]

    # First, just check input files exist and collect their paths so we can
    # compute the cache key from their mtimes/sizes without parsing them.
    de_path = args.data_dir / "deu_sentences.tsv"
    if not de_path.exists():
        log.error(
            "Missing %s. Download:\n  wget https://downloads.tatoeba.org/exports/per_language/deu/deu_sentences.tsv.bz2 && bunzip2 deu_sentences.tsv.bz2",
            de_path,
        )
        return 2

    input_paths: list[Path] = [de_path]
    for iso2 in target_langs:
        iso3 = ISO2_TO_ISO3.get(iso2)
        if not iso3:
            log.error("Unknown target lang %r — add it to ISO2_TO_ISO3", iso2)
            return 2
        tgt_path = args.data_dir / f"{iso3}_sentences.tsv"
        links_path = args.data_dir / f"deu-{iso3}_links.tsv"
        for path, url in [
            (tgt_path, f"https://downloads.tatoeba.org/exports/per_language/{iso3}/{iso3}_sentences.tsv.bz2"),
            (links_path, f"https://downloads.tatoeba.org/exports/per_language/deu/deu-{iso3}_links.tsv.bz2"),
        ]:
            if not path.exists():
                log.error("Missing %s. Download:\n  wget %s && bunzip2 %s.bz2", path, url, path.name)
                return 2
            input_paths.append(path)

    cache_key = _cache_key(args, input_paths)

    rows: list[dict] | None = None
    if not args.rebuild_cache:
        rows = load_cached_rows(args.data_dir, cache_key)

    if rows is None:
        # Cache miss — do the full load + tokenise pipeline
        de_sentences = load_sentences(de_path)
        pairs_by_lang: dict[str, list[tuple[int, str, int, str]]] = {}
        for iso2 in target_langs:
            iso3 = ISO2_TO_ISO3[iso2]
            tgt_sentences = load_sentences(args.data_dir / f"{iso3}_sentences.tsv")
            links = load_links(args.data_dir / f"deu-{iso3}_links.tsv")
            pairs_by_lang[iso2] = build_pairs_for_lang(
                de_sentences, tgt_sentences, links, args.max_len
            )
        rows = index_by_lemma(pairs_by_lang, args.max_per_lemma)
        save_cached_rows(args.data_dir, cache_key, rows)

    if args.dry_run:
        log.info("DRY-RUN — %d rows would be inserted. Sample:", len(rows))
        for r in rows[:5]:
            log.info("  %s [%s]: %s ↔ %s", r["lemma"], r["target_lang"],
                     r["sentence_de"], r["sentence_target"])
        return 0

    inserted = insert_rows(rows)
    log.info("Done. %d rows inserted/upserted.", inserted)
    return 0


if __name__ == "__main__":
    sys.exit(main())
