"""German V2 language module — parallel to languages/german/.

Same detector functions, same per-phenomenon helper methods. Only the
orchestration changes: every detector runs and returns a Candidate
(instead of stopping at first hit), then a Ranker picks the winner.

When the GERMAN_V2_ENABLED flag is on, languages/__init__.py registers
this class as the German module instead of the v1 one. Smoke-test against
the same canonical sentences before rolling out.
"""

import logging

from languages.base import LanguageAnalysis
from languages.german import German as GermanV1
from languages.german.collocations import detect_verb_preposition_collocation
from languages.german.expressions import detect_fixed_expression
from languages.german_v2.nomen_verbs import detect_nomen_verb  # lemma-first matching
from languages.german.verbs import (
    detect_compound_tense,
    detect_modal_verb,
    detect_separable_verb,
    detect_separable_verb_from_prefix,
)
# V2 lassen wrapper compensates for a spaCy lemma quirk on "lässt"/"ließ".
from languages.german_v2.lassen import detect_lassen_construction

from languages.german_v2.compounds import split_compound as split_compound_v2
from languages.german_v2.modal_particles import detect_modal_particle, ParticleInfo
from languages.german_v2.imperative import detect_imperative, ImperativeInfo
from languages.german_v2.zu_infinitive import detect_zu_infinitive, ZuInfInfo
from languages.german_v2.konjunktiv_eins import detect_konjunktiv_eins, KonjunktivIInfo
from languages.german_v2.zustandspassiv import detect_zustandspassiv, ZustandspassivInfo
from languages.german_v2.n_declination import detect_n_declination, NDeklinationInfo
from languages.german_v2.pipeline import Candidate, Ranker

log = logging.getLogger(__name__)


# Per-phenomenon confidence priors. Hand-tuned to reflect how strong each
# signal is — exact dict matches (fixed expressions, NVVs) are the most
# reliable; pattern-based detections (modal+inf, separable verbs) are less
# specific and lose ties against dict matches.
DEFAULT_CONFIDENCE = {
    "fixed_expression": 0.95,
    "nvv": 0.95,
    "collocation": 0.90,
    "lassen": 0.85,
    "compound_tense": 0.85,
    "separable_verb": 0.80,
    "separable_verb_from_prefix": 0.80,
    "modal_verb": 0.80,
    # Particles are pattern-based with no dictionary key — lower confidence
    # so they lose ties to dict-matched phenomena that contain the particle
    # word (e.g. "in den sauren Apfel beißen" beats a "doch" inside it).
    "modal_particle": 0.65,
    # Pure morphology / syntax detectors
    "imperative": 0.85,
    "zu_infinitive": 0.85,
    "konjunktiv_eins": 0.80,
    # Lower than compound_tense so v1's Perfekt reading wins for known
    # intransitive sein-verbs by default; Zustandspassiv only wins when
    # compound_tense is absent (transitive verb + sein + Part II).
    "zustandspassiv": 0.70,
    # Annotation-only: low confidence so it never wins against a real
    # phenomenon (NVV / collocation / etc.). When nothing else fires,
    # it surfaces the n-Deklination rule for learners.
    "n_declination": 0.55,
}


class German(GermanV1):
    """V2 German module: collects all detector matches, ranks, returns best."""

    def __init__(self) -> None:
        super().__init__()
        self._ranker = Ranker()

    def split_compound(self, word: str, lemma: str | None = None) -> list[str] | None:
        """Override v1 with the noun-aware splitter.

        For -end participles we keep v1's specialised path (it has the
        participle-stem validation logic). For everything else we use
        the v2 splitter which:
          - skips known noun lemmas
          - skips inflected forms of known nouns
          - prefers noun candidates over verb infinitives when cleaning
            Fugen-stripped parts
          - recurses deeper for very long compounds
        """
        if lemma and lemma.endswith("end"):
            # Delegate to v1 for participial adjectives — it has dedicated
            # validation that we don't want to re-implement.
            return super().split_compound(word, lemma)
        return split_compound_v2(word)

    def analyze(self, word: str, token, doc, morph: dict[str, str], nlp=None) -> LanguageAnalysis | None:
        candidates: list[Candidate] = []

        # ── Fixed expression ────────────────────────────────────────────
        expression = detect_fixed_expression(token, doc)
        if expression:
            span = 1 + len(expression.related)
            candidates.append(Candidate(
                phenomenon="fixed_expression",
                confidence=DEFAULT_CONFIDENCE["fixed_expression"],
                span_size=span,
                build=lambda e=expression: self._analyze_fixed_expression(word, e),
            ))

        # ── Nomen-Verb-Verbindung ───────────────────────────────────────
        nv = detect_nomen_verb(token, doc)
        if nv:
            span = 1 + len(nv.related)
            candidates.append(Candidate(
                phenomenon="nvv",
                confidence=DEFAULT_CONFIDENCE["nvv"],
                span_size=span,
                build=lambda n=nv: self._analyze_fixed_expression(word, n),
            ))

        # ── Verb + preposition collocation ──────────────────────────────
        collocation = detect_verb_preposition_collocation(token, doc)
        if collocation:
            span = 1 + len(collocation.related)
            candidates.append(Candidate(
                phenomenon="collocation",
                confidence=DEFAULT_CONFIDENCE["collocation"],
                span_size=span,
                build=lambda c=collocation: self._analyze_collocation(word, token, c, morph),
            ))

        # ── lassen + verb ───────────────────────────────────────────────
        lassen = detect_lassen_construction(token, doc)
        if lassen:
            span = 2 + (1 if lassen.has_sich else 0)
            candidates.append(Candidate(
                phenomenon="lassen",
                confidence=DEFAULT_CONFIDENCE["lassen"],
                span_size=span,
                build=lambda l=lassen: self._analyze_lassen(word, l, doc),
            ))

        # ── Separable verb (selected the verb stem) ─────────────────────
        sv_result = detect_separable_verb(token, doc)
        if sv_result:
            infinitive, prefix_ref = sv_result
            candidates.append(Candidate(
                phenomenon="separable_verb",
                confidence=DEFAULT_CONFIDENCE["separable_verb"],
                span_size=2,
                build=lambda inf=infinitive, pr=prefix_ref:
                    self._analyze_separable_from_verb(word, token, inf, pr, morph),
            ))

        # ── Separable verb (selected the prefix/particle) ───────────────
        svp_result = detect_separable_verb_from_prefix(token, doc)
        if svp_result:
            infinitive, verb_text, verb_morph, verb_offset = svp_result
            candidates.append(Candidate(
                phenomenon="separable_verb_from_prefix",
                confidence=DEFAULT_CONFIDENCE["separable_verb_from_prefix"],
                span_size=2,
                build=lambda inf=infinitive, vt=verb_text, vm=verb_morph, vo=verb_offset:
                    self._analyze_separable_from_prefix(word, inf, vt, vm, vo),
            ))

        # ── Compound tense ──────────────────────────────────────────────
        compound_tense = detect_compound_tense(token, doc)
        if compound_tense:
            candidates.append(Candidate(
                phenomenon="compound_tense",
                confidence=DEFAULT_CONFIDENCE["compound_tense"],
                span_size=2,
                build=lambda ct=compound_tense:
                    self._analyze_compound_tense(word, token, ct, morph),
            ))

        # ── Modal verb + infinitive ─────────────────────────────────────
        modal = detect_modal_verb(token, doc)
        if modal:
            span = 2 + (len(modal.cluster) if modal.cluster else 0)
            candidates.append(Candidate(
                phenomenon="modal_verb",
                confidence=DEFAULT_CONFIDENCE["modal_verb"],
                span_size=span,
                build=lambda m=modal: self._analyze_modal_infinitive(word, m),
            ))

        # ── Modal particle (Modalpartikel) ──────────────────────────────
        particle = detect_modal_particle(token, doc)
        if particle:
            candidates.append(Candidate(
                phenomenon="modal_particle",
                confidence=DEFAULT_CONFIDENCE["modal_particle"],
                span_size=1,
                build=lambda p=particle: self._analyze_modal_particle(word, p),
            ))

        # ── Imperativ ───────────────────────────────────────────────────
        imp = detect_imperative(token, doc)
        if imp:
            candidates.append(Candidate(
                phenomenon="imperative",
                confidence=DEFAULT_CONFIDENCE["imperative"],
                span_size=1,
                build=lambda i=imp: self._analyze_imperative(word, i),
            ))

        # ── zu-Infinitiv ────────────────────────────────────────────────
        zu_inf = detect_zu_infinitive(token, doc)
        if zu_inf:
            span = 1 + len(zu_inf.related)
            candidates.append(Candidate(
                phenomenon="zu_infinitive",
                confidence=DEFAULT_CONFIDENCE["zu_infinitive"],
                span_size=span,
                build=lambda z=zu_inf: self._analyze_zu_infinitive(word, z),
            ))

        # ── Konjunktiv I (indirekte Rede) ───────────────────────────────
        k1 = detect_konjunktiv_eins(token, doc)
        if k1:
            candidates.append(Candidate(
                phenomenon="konjunktiv_eins",
                confidence=DEFAULT_CONFIDENCE["konjunktiv_eins"],
                span_size=1,
                build=lambda k=k1: self._analyze_konjunktiv_eins(word, k),
            ))

        # ── Zustandspassiv (sein + Part II) ─────────────────────────────
        zp = detect_zustandspassiv(token, doc)
        if zp:
            candidates.append(Candidate(
                phenomenon="zustandspassiv",
                confidence=DEFAULT_CONFIDENCE["zustandspassiv"],
                span_size=2,
                build=lambda z=zp: self._analyze_zustandspassiv(word, z),
            ))

        # ── n-Deklination (weak masculine nouns) ────────────────────────
        nd = detect_n_declination(token, doc)
        if nd:
            candidates.append(Candidate(
                phenomenon="n_declination",
                confidence=DEFAULT_CONFIDENCE["n_declination"],
                span_size=1,
                build=lambda n=nd: self._analyze_n_declination(word, n),
            ))

        winner = self._ranker.pick(candidates)
        if winner is None:
            return None

        log.debug(
            "[V2] %d candidates: %s — winner: %s (conf=%.2f, span=%d)",
            len(candidates),
            [c.phenomenon for c in candidates],
            winner.phenomenon, winner.confidence, winner.span_size,
        )

        return winner.build()

    def _analyze_imperative(self, word: str, info: ImperativeInfo) -> LanguageAnalysis:
        """Build LanguageAnalysis for an imperative verb form."""
        lemma = info.lemma
        person = info.person_form
        selected_text = word

        def breakdown_fn(analysis, base_translation, extra_translations=None):
            return f"{selected_text} → Imperativ ({person}-form) of {lemma} ({base_translation})"

        return LanguageAnalysis(
            translate=lemma,
            lemma=lemma,
            word_type="imperative",
            related=[],
            pattern=f"{lemma} (Imperativ, {person})",
            llm_hint=f"{lemma} (imperative, addressee: {person})",
            breakdown_fn=breakdown_fn,
        )

    def _analyze_zu_infinitive(self, word: str, info: ZuInfInfo) -> LanguageAnalysis:
        """Build LanguageAnalysis for a zu-Infinitiv construction."""
        infinitive = info.infinitive
        introducer = info.introducer
        selected_text = word

        canonical = (
            f"{introducer} zu {infinitive}" if introducer else f"zu {infinitive}"
        )

        def breakdown_fn(analysis, base_translation, extra_translations=None):
            label = (
                f"{introducer} zu {infinitive}" if introducer else f"zu {infinitive}"
            )
            return f"{selected_text} → zu-Infinitiv: {label} ({base_translation})"

        return LanguageAnalysis(
            translate=infinitive,
            lemma=infinitive,
            word_type="zu_infinitive",
            related=info.related,
            pattern=canonical,
            llm_hint=canonical,
            breakdown_fn=breakdown_fn,
        )

    def _analyze_konjunktiv_eins(self, word: str, info: KonjunktivIInfo) -> LanguageAnalysis:
        """Build LanguageAnalysis for a Konjunktiv I verb form."""
        lemma = info.lemma
        selected_text = word
        person = info.person
        number = info.number
        person_label = (
            f"{person}{'sg' if number == 'Sing' else 'pl' if number == 'Plur' else ''}"
            if person else ""
        )

        def breakdown_fn(analysis, base_translation, extra_translations=None):
            tag = f" {person_label}" if person_label else ""
            return f"{selected_text} → Konjunktiv I{tag} of {lemma} ({base_translation}) — indirekte Rede"

        return LanguageAnalysis(
            translate=lemma,
            lemma=lemma,
            word_type="konjunktiv_eins",
            related=[],
            pattern=f"{lemma} (Konjunktiv I)",
            llm_hint=f"{lemma} in Konjunktiv I (reported speech)",
            breakdown_fn=breakdown_fn,
        )

    def _analyze_zustandspassiv(self, word: str, info: ZustandspassivInfo) -> LanguageAnalysis:
        """Build LanguageAnalysis for a Zustandspassiv (sein + Partizip II as state)."""
        verb_lemma = info.verb_lemma
        sein_text = info.sein_text
        participle = info.participle
        selected_text = word

        # The "other" token is the related token (whichever wasn't selected)
        related: list[TokenRef] = []
        if selected_text.lower() != sein_text.lower():
            related.append(TokenRef(sein_text, info.sein_idx))
        if selected_text.lower() != participle.lower():
            related.append(TokenRef(participle, info.participle_idx))

        canonical = f"{sein_text} {participle}"

        def breakdown_fn(analysis, base_translation, extra_translations=None):
            return (
                f"{sein_text} + {participle} → Zustandspassiv "
                f"(state from {verb_lemma}, {base_translation})"
            )

        return LanguageAnalysis(
            translate=verb_lemma,
            lemma=verb_lemma,
            word_type="zustandspassiv",
            related=related,
            pattern=canonical,
            llm_hint=f"Zustandspassiv: {canonical} (state, not action)",
            breakdown_fn=breakdown_fn,
        )

    def _analyze_n_declination(self, word: str, info: NDeklinationInfo) -> LanguageAnalysis:
        """Build LanguageAnalysis for an n-Deklination noun.

        The point isn't to translate (regular noun translation suffices)
        but to surface the morphological rule: weak masculine nouns add
        -n / -en in every case except nominative singular.
        """
        lemma = info.lemma
        surface = info.surface
        rule = (
            "n-Deklination: weak masculine — adds -n/-en in every case "
            "except nominative singular"
        )

        def breakdown_fn(analysis, base_translation, extra_translations=None):
            if info.is_lemma_form:
                return f"{surface} ({base_translation}) — {rule}"
            return f"{surface} → {lemma} ({base_translation}) — {rule}"

        return LanguageAnalysis(
            translate=lemma,
            lemma=lemma,
            word_type="n_declination",
            related=[],
            pattern=lemma,
            llm_hint=f"{lemma} (n-Deklination weak masculine)",
            breakdown_fn=breakdown_fn,
        )

    def _analyze_modal_particle(self, word: str, info: ParticleInfo) -> LanguageAnalysis:
        """Build LanguageAnalysis for a German modal particle.

        The particle has no lexical translation — its job is pragmatic. We
        pass the (sentence-type-aware) reading to the translator as both the
        canonical hint and the breakdown text, so the LLM doesn't try to
        translate it as a literal word.
        """
        canonical = info.canonical
        reading = info.reading
        sentence_type = info.sentence_type
        selected_text = word

        def breakdown_fn(analysis, base_translation, extra_translations=None):
            return f"{selected_text} ({sentence_type}) → Modalpartikel: {reading}"

        return LanguageAnalysis(
            translate=info.particle_text,
            lemma=info.particle_text,
            word_type="modal_particle",
            related=[],
            pattern=canonical,
            llm_hint=canonical,
            breakdown_fn=breakdown_fn,
        )
