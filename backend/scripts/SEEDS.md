# Seeding the German dictionaries from external resources

This directory hosts one-shot loaders that pull German linguistic data
from open sources into the `german_*` tables (migrations 005, 006).

Every seeded row is tagged with a `source` column so we can roll back
or re-attribute imports later. Re-runs are idempotent (upserts).

## Order of operations (first time setup)

1. Apply migrations:
   - `supabase/migrations/005_german_dictionaries.sql`
   - `supabase/migrations/006_german_external_seeds.sql`

2. Import the hand-curated v1 dicts:
   ```
   cd backend
   python -m scripts.import_german_dicts
   ```

3. Download the external dumps into `backend/scripts/seed_data/`
   (see per-source instructions below).

4. Run the seeders. Each supports `--dry-run` for previewing.

5. Restart the backend. Startup log should report
   `Loaded German dicts from DB: …` with higher counts than before.

---

## Sources

### 1. Tatoeba — bilingual sentence examples

- **URL**: <https://tatoeba.org>, per-language pair dumps at
  <https://downloads.tatoeba.org/exports/per_language/>
- **License**: CC BY 2.0 FR. Attribution required if redistributed.
- **Why per-language**: the global `sentences.tar.bz2` covers 400+
  languages (~13M rows, ~GBs). The per-language exports are a few MB
  each. Tatoeba doesn't ship pre-aligned bilingual files, so we still
  join sentences ↔ links — but on small per-language files.
- **Download** — German sentences (used by every pair) plus, per
  target language, the target's sentences and the DE↔target links file.
  The extension exposes 10 target languages (en, es, fr, it, pt, zh,
  ja, ko, ar, ru); seed all of them so any user gets attested examples.

  ```bash
  cd backend/scripts/seed_data
  BASE=https://downloads.tatoeba.org/exports/per_language

  # German source — used by every pair (~11MB)
  wget $BASE/deu/deu_sentences.tsv.bz2

  # Per-target: sentences + DE↔target links. Each pair is a few MB.
  # 2-letter → Tatoeba ISO 639-3 mapping:
  #   en→eng  es→spa  fr→fra  it→ita  pt→por
  #   zh→cmn  ja→jpn  ko→kor  ar→ara  ru→rus
  for iso3 in eng spa fra ita por cmn jpn kor ara rus; do
    wget $BASE/$iso3/${iso3}_sentences.tsv.bz2
    wget $BASE/deu/deu-${iso3}_links.tsv.bz2
  done

  bunzip2 *.bz2
  ```
- **Run**:
  ```bash
  cd backend
  python -m scripts.seed_tatoeba --dry-run                  # preview all 10 targets
  python -m scripts.seed_tatoeba                            # all 10 targets
  python -m scripts.seed_tatoeba --target-langs en,fr,es    # subset
  ```
- **Result**: rows in `german_bilingual_example` keyed by lemma. The
  translator can pull a few attested examples for any word the user
  selects.
- **Attribution**: every row has `source='tatoeba'` and a Tatoeba
  pair id (`<de_id>-<tgt_id>`) in `external_id`. Surface
  "from Tatoeba (CC BY 2.0 FR)" whenever this data appears in the UI.

### 2. Kaikki/Wiktionary — idioms (Redewendungen)

- **URL**: <https://kaikki.org/dictionary/German/>
- **License**: CC BY-SA 4.0 (Wiktionary). Attribution + share-alike if
  redistributed.
- **Download**:
  ```
  cd backend/scripts/seed_data
  wget https://kaikki.org/dictionary/German/kaikki.org-dictionary-German.jsonl
  ```
- **Run**:
  ```
  cd backend
  python -m scripts.seed_kaikki_idioms --dry-run
  python -m scripts.seed_kaikki_idioms
  ```
- **Result**: rows in `german_expression` with `figurative=true`,
  `source='kaikki_wiktionary'`. Detected by the same fixed-expression
  matcher as plain expressions; the figurative flag tells the
  response layer to surface a paraphrase rather than a literal gloss.

### 3. Kaikki/Wiktionary — pre-loaded translations

- **URL / License**: same as (2) — reuses the JSONL dump.
- **Run** (apply migration `008_german_translation.sql` first):
  ```bash
  cd backend
  python -m scripts.seed_kaikki_translations --dry-run
  python -m scripts.seed_kaikki_translations
  ```
- **Result**: rows in `german_translation` keyed by
  `(lemma, pos, sense_id, target_lang, translation)`. Covers the 10
  target languages the extension exposes (en, es, fr, it, pt, zh, ja,
  ko, ar, ru). `sense_id` stays NULL until the sense table is built —
  the unique constraint uses `NULLS NOT DISTINCT` so re-runs stay
  idempotent.
- **What it unblocks**: unambiguous word lookups (Hund → "dog") return
  from the DB in ~10ms instead of going to the LLM. Polysemes still
  fall through to the LLM until WSD is built.

### 4. Kaikki/Wiktionary — sense list (foundation for WSD)

- **URL / License**: same as (2).
- **Run** (apply migration `009_german_sense.sql` first):
  ```bash
  cd backend
  python -m scripts.seed_kaikki_senses --dry-run
  python -m scripts.seed_kaikki_senses
  ```
- **Result**: rows in `german_sense` keyed by
  `(lemma, pos, sense_id)`. Every German lemma's distinct meanings get
  their own row with `gloss`, `examples`, and `tags` (intransitive,
  colloquial, formal, …). `sense_id` is Wiktionary's stable id so
  re-runs are idempotent.
- **What it unblocks**: word-sense disambiguation (build-step 4 of the
  V2 master plan — biggest single quality lever). Side benefit: the
  English glosses are usable as candidate EN translations until we
  have a proper translation source.

### 5. OpenThesaurus — German synonym groups

- **URL**: <https://www.openthesaurus.de/about/download>
- **License**: CC BY-SA 4.0 / LGPL — credit "OpenThesaurus.de" in
  the UI when this data is shown.
- **Download**:
  ```bash
  cd backend/scripts/seed_data
  wget https://www.openthesaurus.de/export/OpenThesaurus-Textversion.zip
  unzip OpenThesaurus-Textversion.zip
  ```
- **Run** (apply migration `011_german_synonym_group.sql` first):
  ```bash
  cd backend
  python -m scripts.seed_openthesaurus --dry-run
  python -m scripts.seed_openthesaurus
  ```
- **Result**: rows in `german_synonym_group` — each row is one cluster
  of synonyms (e.g. `{groß, riesig, enorm, mächtig, ausgedehnt}`). GIN
  index on `members` for fast "which group(s) contain this word?"
  lookup.
- **What it unblocks**: WSD support (same word + same synonym cluster
  = same sense in different sentences); UI "other ways to say this".

### 6. Frequency rankings (OpenSubtitles 2018 via HermitDave)

- **URL**: <https://github.com/hermitdave/FrequencyWords>
- **License**: CC-BY-SA 4.0. Surface "OpenSubtitles 2018 / HermitDave
  FrequencyWords (CC-BY-SA 4.0)" in the UI when this data is shown.
- **Why this and not DWDS**: DWDS doesn't publish a downloadable list
  directly. HermitDave's repo gives a clean `word count` TSV, sorted
  by descending frequency, derived from OpenSubtitles 2018.
- **Download**:
  ```bash
  cd backend/scripts/seed_data
  wget https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/de/de_50k.txt
  ```
- **Run** (apply migration `012_german_frequency.sql` first):
  ```bash
  cd backend
  python -m scripts.seed_frequency --dry-run
  python -m scripts.seed_frequency
  ```
- **Result**: 50k rows in `german_frequency(word, rank, count, bucket)`.
  Buckets: A (top 1k) / B (top 5k) / C (top 20k) / D (top 50k).
  Anything not in the table is treated as rank > 50k = rare.
- **Caveat**: this is *surface form* frequency, not lemma frequency.
  *ging* and *gehen* are separate rows. For lemma-level frequency,
  take `max(count)` across the lemma's surface forms at query time.

### 7. Kaikki/Wiktionary — verb forms + noun gender/plural

- **URL / License**: same as the other Kaikki sections.
- **Run** (apply migration `013_german_morphology.sql` first):
  ```bash
  cd backend
  python -m scripts.seed_kaikki_forms --dry-run
  python -m scripts.seed_kaikki_forms
  ```
- **Result**:
  - `german_verb_form(surface, lemma, tags[])` — every inflected verb
    surface form with its morphology tags. Replaces the simplemma
    + spaCy lemmatisation round-trip at request time.
  - `german_noun(lemma, gender, plural)` — gender + plural per lemma.
    A noun with multiple genders (e.g. *Band* m / f / n) gets one
    row per gender.
- **What it unblocks**:
  - Direct surface→lemma lookup without a parser call
  - Noun-gender annotations in breakdown output
  - n-Deklination detector (Mensch/Student/Junge type)

### 8. Kaikki/Wiktionary — verb+preposition collocations

- **URL / License**: same as (2).
- **Download**: same JSONL as (2) — no extra download.
- **Run**:
  ```
  cd backend
  python -m scripts.seed_kaikki_collocations --dry-run
  python -m scripts.seed_kaikki_collocations
  ```
- **Result**: rows in `german_collocation` tagged
  `source='kaikki_wiktionary'`. Conservative extraction (gloss
  patterns + example-window scan) to keep noise out.

---

## Coverage expectations

After seeding everything:

| Table | curated_v1 | + tatoeba | + kaikki idioms | + kaikki collocs |
|---|---|---|---|---|
| `german_nvv` | ~735 | ~735 | ~735 | ~735 |
| `german_expression` | ~833 | ~833 | several thousand | several thousand |
| `german_collocation` | ~857 | ~857 | ~857 | ~2–3× |
| `german_bilingual_example` | 0 | ~50–200k rows | … | … |

Tatoeba volume depends on `--max-per-lemma` (default 5 per lemma per
target lang).

---

## Rolling back a bad import

Every row has a `source` and a `created_at`. To undo a Kaikki idiom run:

```sql
delete from public.german_expression
where source = 'kaikki_wiktionary' and created_at > '2026-04-29';
```

---

## Adding a new source

1. Pick a stable `source` slug (`'opus_subtitles'`, `'dwds_collocs'`, …).
2. Write a `seed_<source>.py` next to the existing ones.
3. Use `--dry-run` to validate sample rows before any insert.
4. Document license + attribution rules in this file.
5. Re-run dry-run on a sample, sanity-check, then full import.
