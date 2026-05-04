"""In-memory store for the German dictionaries.

Loaded from Postgres at app startup via load(). Detectors import the
public state from this module — they're agnostic to where the data
came from.

Public state (mutated in place by load()):
    NOMEN_VERB                       dict[(noun, verb_lemma) -> canonical]
    NOMEN_VERB_PREP                  dict[(prep, noun, verb_lemma) -> canonical]
    NOMEN_VERB_REFLEXIVE             set[(noun, verb_lemma)]
    NOMEN_VERB_PREP_REFLEXIVE        dict[(prep, noun, verb_lemma) -> canonical]
    NOMEN_VERB_INDEX                 dict[noun_lower -> list[(noun, verb_lemma)]]
    NOMEN_VERB_PREP_INDEX            dict[noun_lower -> list[(prep, noun, verb)]]
    NOMEN_VERB_PREP_REFLEXIVE_INDEX  dict[noun_lower -> list[(prep, noun, verb)]]
    FIXED_EXPRESSIONS                dict[tuple[str, ...] -> canonical]
    EXPRESSION_INDEX                 dict[word_lower -> list[tuple[str, ...]]]
    FIGURATIVE_EXPRESSIONS           set[tuple[str, ...]]
    EXPRESSION_MEANINGS              dict[tuple[str, ...] -> {meaning_de, meaning_targets}]
    VERB_PREPOSITION_COLLOCATIONS    dict[(verb_lemma, prep) -> pattern]
"""

import logging

log = logging.getLogger(__name__)

# Public state — mutated in place by loaders
NOMEN_VERB: dict[tuple[str, str], str] = {}
NOMEN_VERB_PREP: dict[tuple[str, str, str], str] = {}
NOMEN_VERB_REFLEXIVE: set[tuple[str, str]] = set()
NOMEN_VERB_PREP_REFLEXIVE: dict[tuple[str, str, str], str] = {}
NOMEN_VERB_INDEX: dict[str, list[tuple[str, str]]] = {}
NOMEN_VERB_PREP_INDEX: dict[str, list[tuple[str, str, str]]] = {}
NOMEN_VERB_PREP_REFLEXIVE_INDEX: dict[str, list[tuple[str, str, str]]] = {}

FIXED_EXPRESSIONS: dict[tuple[str, ...], str] = {}
EXPRESSION_INDEX: dict[str, list[tuple[str, ...]]] = {}

# Tokens-key → metadata for figurative entries (idioms from Wiktionary).
# Empty for plain fixed expressions. Used by the response layer to mark
# idioms and surface paraphrases.
FIGURATIVE_EXPRESSIONS: set[tuple[str, ...]] = set()
EXPRESSION_MEANINGS: dict[tuple[str, ...], dict] = {}  # tokens → {meaning_de, meaning_targets}

VERB_PREPOSITION_COLLOCATIONS: dict[tuple[str, str], str] = {}


def _build_indexes() -> None:
    """Rebuild the reverse indexes from the primary dicts."""
    NOMEN_VERB_INDEX.clear()
    for (noun, verb_lemma) in NOMEN_VERB:
        NOMEN_VERB_INDEX.setdefault(noun.lower(), []).append((noun, verb_lemma))

    NOMEN_VERB_PREP_INDEX.clear()
    for (prep, noun, verb_lemma) in NOMEN_VERB_PREP:
        NOMEN_VERB_PREP_INDEX.setdefault(noun.lower(), []).append((prep, noun, verb_lemma))

    NOMEN_VERB_PREP_REFLEXIVE_INDEX.clear()
    for (prep, noun, verb_lemma) in NOMEN_VERB_PREP_REFLEXIVE:
        NOMEN_VERB_PREP_REFLEXIVE_INDEX.setdefault(noun.lower(), []).append((prep, noun, verb_lemma))

    EXPRESSION_INDEX.clear()
    for tokens in FIXED_EXPRESSIONS:
        for word in tokens:
            EXPRESSION_INDEX.setdefault(word.lower(), []).append(tokens)


_PAGE = 1000  # PostgREST default max-rows-per-request


def _fetch_all(db, table: str, columns: str) -> list[dict]:
    """Page through a table until no more rows come back.

    PostgREST caps each request at ~1000 rows; without pagination we
    silently truncate to the first page. Walk in fixed-size pages and
    stop when a short page tells us we're done.
    """
    rows: list[dict] = []
    start = 0
    while True:
        page = (
            db.table(table)
            .select(columns)
            .range(start, start + _PAGE - 1)
            .execute()
            .data
            or []
        )
        rows.extend(page)
        if len(page) < _PAGE:
            return rows
        start += _PAGE


def load() -> None:
    """Load the German dictionaries from Postgres into memory.

    Raises if the DB is unreachable or any dictionary table comes back
    empty. The app cannot serve translations without this data, so we
    fail loudly at startup rather than silently using stale or empty
    state.
    """
    from db import get_db

    db = get_db()

    nvv_rows = _fetch_all(db, "german_nvv",
                          "noun, verb_lemma, prep_lemma, canonical, requires_sich")
    expr_rows = _fetch_all(db, "german_expression",
                           "tokens, canonical, figurative, meaning_de, meaning_targets")
    coll_rows = _fetch_all(db, "german_collocation",
                           "verb_lemma, preposition, pattern")

    if not nvv_rows or not expr_rows or not coll_rows:
        raise RuntimeError(
            f"DB returned empty result for one or more German dictionaries "
            f"(nvv={len(nvv_rows)}, expr={len(expr_rows)}, coll={len(coll_rows)}). "
            "Migrations 005/006 may not be applied or the curated_v1 import "
            "may not have run."
        )

    NOMEN_VERB.clear()
    NOMEN_VERB_PREP.clear()
    NOMEN_VERB_REFLEXIVE.clear()
    NOMEN_VERB_PREP_REFLEXIVE.clear()

    for r in nvv_rows:
        noun = r["noun"]
        verb_lemma = r["verb_lemma"]
        prep_lemma = r["prep_lemma"]
        canonical = r["canonical"]
        requires_sich = r["requires_sich"]

        if prep_lemma is None:
            NOMEN_VERB[(noun, verb_lemma)] = canonical
            if requires_sich:
                NOMEN_VERB_REFLEXIVE.add((noun, verb_lemma))
        elif requires_sich:
            NOMEN_VERB_PREP_REFLEXIVE[(prep_lemma, noun, verb_lemma)] = canonical
        else:
            NOMEN_VERB_PREP[(prep_lemma, noun, verb_lemma)] = canonical

    FIXED_EXPRESSIONS.clear()
    FIGURATIVE_EXPRESSIONS.clear()
    EXPRESSION_MEANINGS.clear()
    for r in expr_rows:
        tokens = tuple(r["tokens"])
        FIXED_EXPRESSIONS[tokens] = r["canonical"]
        if r.get("figurative"):
            FIGURATIVE_EXPRESSIONS.add(tokens)
        meaning_de = r.get("meaning_de")
        meaning_targets = r.get("meaning_targets")
        if meaning_de or meaning_targets:
            EXPRESSION_MEANINGS[tokens] = {
                "meaning_de": meaning_de,
                "meaning_targets": meaning_targets,
            }

    VERB_PREPOSITION_COLLOCATIONS.clear()
    for r in coll_rows:
        VERB_PREPOSITION_COLLOCATIONS[(r["verb_lemma"], r["preposition"])] = r["pattern"]

    _build_indexes()

    log.info(
        "Loaded German dicts from DB: %d NVV / %d NVV+prep / %d NVV+prep+sich / "
        "%d expressions (%d figurative) / %d collocations",
        len(NOMEN_VERB), len(NOMEN_VERB_PREP), len(NOMEN_VERB_PREP_REFLEXIVE),
        len(FIXED_EXPRESSIONS), len(FIGURATIVE_EXPRESSIONS),
        len(VERB_PREPOSITION_COLLOCATIONS),
    )
