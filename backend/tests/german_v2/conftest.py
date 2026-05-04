"""Fixtures for the V2 corpus tests.

The corpus runs against the v2 German module (parallel to v1). We
hot-load the dictionary store from Postgres once per session and
override any DB-only data tables that the local environment hasn't
migrated yet (modal particles, n-Deklination).
"""

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def load_dict_store():
    """Load Postgres-backed dictionaries; backfill V2-only tables from
    seed JSONs when migrations 014/015 aren't applied locally."""
    from languages.german import dict_store

    dict_store.load()

    seed_dir = Path(__file__).parent.parent.parent / "scripts" / "seed_data"

    if not dict_store.MODAL_PARTICLES:
        path = seed_dir / "modal_particles.json"
        if path.exists():
            for e in json.loads(path.read_text())["particles"]:
                dict_store.MODAL_PARTICLES[(e["particle"].lower(), e["sentence_type"])] = e["reading"]

    if not dict_store.N_DECL_LEMMAS:
        path = seed_dir / "n_declination.json"
        if path.exists():
            for lemma in json.loads(path.read_text())["lemmas"]:
                dict_store.N_DECL_LEMMAS.add(lemma)
