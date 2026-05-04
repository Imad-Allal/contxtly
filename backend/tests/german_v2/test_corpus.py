"""Per-phenomenon gold-sentence corpus for the V2 German module.

Loads every JSON file under cases/ and runs the v2 analyzer against
each (sentence, target) pair. Asserts that:
  - detected==True cases produce a non-None LanguageAnalysis
  - detected==False cases produce None
  - canonical_contains/word_type_contains substring assertions match

Overall accuracy gate: ≥95%. Individual failures are logged but only
the gate fails the suite, so coverage gaps are visible without
blocking dev iteration.
"""

import json
from pathlib import Path

import pytest
import spacy

from languages.german_v2 import German

CASES_DIR = Path(__file__).parent / "cases"
ACCURACY_GATE = 0.95


@pytest.fixture(scope="session")
def german_v2():
    return German()


@pytest.fixture(scope="session")
def nlp():
    return spacy.load("de_core_news_lg")


def _all_cases():
    """Yield (file_stem, case_dict) for every case in every JSON file."""
    out = []
    for json_path in sorted(CASES_DIR.glob("*.json")):
        data = json.loads(json_path.read_text())
        for case in data.get("cases", []):
            out.append((json_path.stem, case))
    return out


def _parse_morph(token) -> dict[str, str]:
    """Same shape as analyzer.parse_morphology but inlined to avoid pulling
    in the full analyzer (which imports langdetect, spacy models, etc.)."""
    out: dict[str, str] = {}
    for item in token.morph:
        if "=" in item:
            k, v = item.split("=", 1)
            out[k] = v
    return out


def _run_case(german_v2, nlp, case):
    """Run one case; return (passed: bool, message_on_fail: str | None)."""
    sentence = case["sentence"]
    target_word = case["target"]
    expect = case["expect"]

    doc = nlp(sentence)
    # Match by surface first; fall back to lemma so cases can use either
    # form (the user typically clicks a surface form, but corpus authors
    # find lemmas more readable).
    target_lower = target_word.lower()
    target = next(
        (t for t in doc if t.text.lower() == target_lower),
        None,
    )
    if target is None:
        target = next(
            (t for t in doc if (t.lemma_ or "").lower() == target_lower),
            None,
        )
    if target is None:
        return False, f"target {target_word!r} not found in tokens of {sentence!r}"

    morph = _parse_morph(target)
    analysis = german_v2.analyze(target.text, target, doc, morph, nlp)
    detected = analysis is not None

    if detected != expect.get("detected", True):
        return False, (
            f"sentence={sentence!r} target={target_word!r}: "
            f"expected detected={expect.get('detected')}, got detected={detected} "
            f"(analysis={analysis})"
        )

    if detected and analysis is not None:
        canonical = (analysis.pattern or analysis.lemma or "").lower()
        if "canonical_contains" in expect:
            sub = expect["canonical_contains"].lower()
            if sub not in canonical:
                return False, (
                    f"sentence={sentence!r} target={target_word!r}: "
                    f"canonical {canonical!r} does not contain {sub!r}"
                )
        if "word_type_contains" in expect:
            wt = (analysis.word_type or "").lower()
            sub = expect["word_type_contains"].lower()
            if sub not in wt:
                return False, (
                    f"sentence={sentence!r} target={target_word!r}: "
                    f"word_type {wt!r} does not contain {sub!r}"
                )

    return True, None


def test_overall_accuracy(german_v2, nlp):
    """Run the whole corpus, assert overall accuracy ≥ ACCURACY_GATE."""
    cases = _all_cases()
    if not cases:
        pytest.skip("no test cases found in cases/")

    passed = 0
    failures: list[str] = []
    per_file: dict[str, list[bool]] = {}

    for file_stem, case in cases:
        ok, msg = _run_case(german_v2, nlp, case)
        per_file.setdefault(file_stem, []).append(ok)
        if ok:
            passed += 1
        else:
            failures.append(f"  [{file_stem}] {msg}")

    total = len(cases)
    accuracy = passed / total if total else 0.0

    print(f"\n=== V2 corpus: {passed}/{total} passed ({accuracy:.1%}) ===")
    for file_stem, results in sorted(per_file.items()):
        sub_pass = sum(results)
        sub_total = len(results)
        print(f"  {file_stem:22}  {sub_pass}/{sub_total}")
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f)

    assert accuracy >= ACCURACY_GATE, (
        f"V2 corpus accuracy {accuracy:.1%} below gate {ACCURACY_GATE:.0%} "
        f"({passed}/{total} passed; {len(failures)} failures — see stdout)"
    )
