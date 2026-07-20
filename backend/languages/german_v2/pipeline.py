"""V2 detection pipeline: candidates + ranker.

Replaces v1's first-hit cascade. Every detector emits 0..N Candidate
records; the Ranker picks the winner. Down the line the same machinery
will return a *stack* (modal + passive + separable verb on the same
head, etc.) instead of a single winner — for now we keep the contract
identical to v1 (one LanguageAnalysis returned) so the rest of the
backend doesn't need changes.

A Candidate is intentionally lightweight:
    - phenomenon: a string slug for ranking and telemetry
    - confidence: 0..1, set per-detector based on how strong the signal is
    - span_size: number of tokens covered (longer wins ties)
    - build:     callable that constructs the LanguageAnalysis when chosen
                 (lazy — we don't pay for building the analysis until the
                 ranker actually picks the candidate)
"""

from dataclasses import dataclass
from typing import Callable

from languages.base import LanguageAnalysis


@dataclass
class Candidate:
    phenomenon: str
    confidence: float
    span_size: int
    build: Callable[[], LanguageAnalysis]


class Ranker:
    """Picks the best Candidate from a list.

    Strategy v0 — highest confidence × longest span. Ties broken by
    phenomenon order in PHENOMENON_PRIORITY (stable, deterministic).

    Future iterations can:
      - Prefer candidates whose span contains the user-selected token
      - Compose multiple non-overlapping candidates into a stack
      - Use telemetry-derived confidences instead of static defaults
    """

    # Tiebreaker when (confidence, span_size) tie — earlier in the list wins.
    PHENOMENON_PRIORITY = [
        "fixed_expression",
        "nvv",
        "collocation",
        "lassen",
        "separable_verb",
        "separable_verb_from_prefix",
        "compound_tense",
        "modal_verb",
        "imperative",
        "zu_infinitive",
        "konjunktiv_eins",
        "zustandspassiv",
        "modal_particle",
        "n_declination",
    ]

    def pick(self, candidates: list[Candidate]) -> Candidate | None:
        if not candidates:
            return None

        priority_idx = {p: i for i, p in enumerate(self.PHENOMENON_PRIORITY)}

        def sort_key(c: Candidate):
            return (
                c.confidence,
                c.span_size,
                -priority_idx.get(c.phenomenon, len(self.PHENOMENON_PRIORITY)),
            )

        return max(candidates, key=sort_key)
