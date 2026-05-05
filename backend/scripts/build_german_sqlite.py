import argparse
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

from db import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "data" / "german.sqlite"
PAGE = 1000
INSERT_BATCH = 1000

TABLES: dict[str, dict] = {
    "german_nvv": {
        "ddl": """
            create table german_nvv (
                noun           text not null,
                verb_lemma     text not null,
                prep_lemma     text,
                canonical      text not null,
                requires_sich  integer not null default 0
            );
            create index german_nvv_noun_lower_idx on german_nvv (lower(noun));
            create index german_nvv_verb_idx on german_nvv (verb_lemma);
        """,
        "columns": "noun, verb_lemma, prep_lemma, canonical, requires_sich",
        "json_cols": [],
    },
    "german_expression": {
        "ddl": """
            create table german_expression (
                tokens           text not null,        -- JSON array
                canonical        text not null,
                figurative       integer not null default 0,
                meaning_de       text,
                meaning_targets  text                  -- JSON object or null
            );
        """,
        "columns": "tokens, canonical, figurative, meaning_de, meaning_targets",
        "json_cols": ["tokens", "meaning_targets"],
    },
    "german_collocation": {
        "ddl": """
            create table german_collocation (
                verb_lemma   text not null,
                preposition  text not null,
                pattern      text not null
            );
            create index german_collocation_verb_idx on german_collocation (verb_lemma);
        """,
        "columns": "verb_lemma, preposition, pattern",
        "json_cols": [],
    },
    "german_modal_particle": {
        "ddl": """
            create table german_modal_particle (
                particle       text not null,
                sentence_type  text not null,
                reading        text not null
            );
            create index german_modal_particle_particle_idx on german_modal_particle (particle);
        """,
        "columns": "particle, sentence_type, reading",
        "json_cols": [],
    },
    "german_noun": {
        "ddl": """
            create table german_noun (
                lemma   text not null,
                gender  text,
                plural  text
            );
            create index german_noun_lemma_idx on german_noun (lemma);
        """,
        "columns": "lemma, gender, plural",
        "json_cols": [],
    },
    "german_n_decl": {
        "ddl": """
            create table german_n_decl (
                lemma  text primary key
            );
        """,
        "columns": "lemma",
        "json_cols": [],
    },
    # ── On-demand tables (queried at request time, not loaded into RAM) ──
    "german_sense": {
        "ddl": """
            create table german_sense (
                lemma        text not null,
                pos          text,
                sense_id     text not null,
                gloss        text not null,
                gloss_extra  text,                     -- JSON array
                examples     text,                     -- JSON array
                tags         text                      -- JSON array
            );
            create index german_sense_lemma_idx on german_sense (lemma);
            create index german_sense_lemma_pos_idx on german_sense (lemma, pos);
        """,
        "columns": "lemma, pos, sense_id, gloss, gloss_extra, examples, tags",
        "json_cols": ["gloss_extra", "examples", "tags"],
    },
    "german_translation": {
        "ddl": """
            create table german_translation (
                lemma        text not null,
                pos          text,
                sense_id     text,
                target_lang  text not null,
                translation  text not null
            );
            create index german_translation_lemma_lang_idx on german_translation (lemma, target_lang);
        """,
        "columns": "lemma, pos, sense_id, target_lang, translation",
        "json_cols": [],
    },
    "german_bilingual_example": {
        "ddl": """
            create table german_bilingual_example (
                lemma            text not null,
                sentence_de      text not null,
                sentence_target  text not null,
                target_lang      text not null
            );
            create index german_bilingual_example_lemma_lang_idx
                on german_bilingual_example (lemma, target_lang);
        """,
        "columns": "lemma, sentence_de, sentence_target, target_lang",
        "json_cols": [],
    },
    "german_frequency": {
        "ddl": """
            create table german_frequency (
                word    text primary key,
                rank    integer not null,
                count   integer not null,
                bucket  text not null
            );
            create index german_frequency_rank_idx on german_frequency (rank);
        """,
        "columns": "word, rank, count, bucket",
        "json_cols": [],
        # No `id` column; PK is `word`. Pagination uses keyset on `word`.
        "keyset_col": "word",
    },
    "german_synonym_group": {
        "ddl": """
            create table german_synonym_group (
                members  text not null              -- JSON array
            );
        """,
        "columns": "members",
        "json_cols": ["members"],
    },
    "german_verb_form": {
        "ddl": """
            create table german_verb_form (
                surface  text not null,
                lemma    text not null,
                tags     text                       -- JSON array
            );
            create index german_verb_form_surface_idx on german_verb_form (surface);
            create index german_verb_form_lemma_idx on german_verb_form (lemma);
        """,
        "columns": "surface, lemma, tags",
        "json_cols": ["tags"],
    },
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT,
                   help="Output SQLite path (default: backend/data/german.sqlite)")
    p.add_argument("--only", default="",
                   help="Comma-separated table names to copy (default: all)")
    p.add_argument("--skip", default="",
                   help="Comma-separated table names to skip")
    return p.parse_args()


def _page_table(db, table: str, columns: str, keyset_col: str = "id"):
    selected_cols = columns
    if keyset_col not in [c.strip() for c in columns.split(",")]:
        selected_cols = f"{keyset_col}, {columns}"

    # Numeric keysets start at -1; text keysets start before any real value.
    last = -1 if keyset_col == "id" else ""

    while True:
        page = (
            db.table(table)
            .select(selected_cols)
            .gt(keyset_col, last)
            .order(keyset_col)
            .limit(PAGE)
            .execute()
            .data
            or []
        )
        if not page:
            return
        for row in page:
            # Strip the keyset col from yielded rows if it wasn't requested
            if keyset_col not in [c.strip() for c in columns.split(",")]:
                row = {k: v for k, v in row.items() if k != keyset_col}
            yield row
        if len(page) < PAGE:
            return
        last = page[-1][keyset_col]


def _normalise_row(row: dict, columns: list[str], json_cols: set[str]) -> tuple:
    """Convert a Supabase row into a positional tuple ready for INSERT."""
    out = []
    for col in columns:
        v = row.get(col)
        if col in json_cols and v is not None:
            v = json.dumps(v, ensure_ascii=False)
        # SQLite stores booleans as integers
        if isinstance(v, bool):
            v = 1 if v else 0
        out.append(v)
    return tuple(out)


def _copy_table(conn: sqlite3.Connection, db, table: str, spec: dict) -> int:
    """Copy one Supabase table into SQLite. Returns row count."""
    log.info("→ %s", table)

    # Drop + recreate
    conn.executescript(f"drop table if exists {table};")
    conn.executescript(spec["ddl"])

    columns = [c.strip() for c in spec["columns"].split(",")]
    json_cols = set(spec["json_cols"])
    placeholders = ",".join(["?"] * len(columns))
    insert_sql = f"insert into {table} ({','.join(columns)}) values ({placeholders})"

    buffer: list[tuple] = []
    inserted = 0
    t0 = time.time()

    try:
        keyset_col = spec.get("keyset_col", "id")
        for row in _page_table(db, table, spec["columns"], keyset_col):
            buffer.append(_normalise_row(row, columns, json_cols))
            if len(buffer) >= INSERT_BATCH:
                conn.executemany(insert_sql, buffer)
                inserted += len(buffer)
                buffer.clear()
                if inserted % 50000 == 0:
                    log.info("    …%d", inserted)
        if buffer:
            conn.executemany(insert_sql, buffer)
            inserted += len(buffer)
    except Exception as e:
        log.warning("  failed (%s) — table may not exist on this Supabase project; skipping", e)
        conn.rollback()
        return 0

    conn.commit()
    log.info("  %d rows in %.1fs", inserted, time.time() - t0)
    return inserted


def main() -> int:
    args = parse_args()
    out_path: Path = args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    only = {t.strip() for t in args.only.split(",") if t.strip()}
    skip = {t.strip() for t in args.skip.split(",") if t.strip()}

    if out_path.exists():
        out_path.unlink()
        log.info("Removed existing %s", out_path)

    db = get_db()
    conn = sqlite3.connect(out_path)
    conn.execute("pragma journal_mode = wal;")
    conn.execute("pragma synchronous = normal;")

    total = 0
    for table, spec in TABLES.items():
        if only and table not in only:
            continue
        if table in skip:
            continue
        total += _copy_table(conn, db, table, spec)

    log.info("Vacuuming…")
    conn.execute("vacuum;")
    conn.close()

    size_mb = out_path.stat().st_size / (1024 * 1024)
    log.info("Done. %d total rows. %.1f MB at %s", total, size_mb, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
