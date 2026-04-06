"""
Accuracy threshold tests.

Runs all cases from test_german_analysis, counts pass/fail,
prints every failure, and asserts >= 90% accuracy overall.
Individual failures are visible but don't fail the suite on their own.
"""

import pytest
from analyzer import analyze_word
from languages.german.compounds import split_compound

from tests.test_german_analysis import (
    COMPOUND_SPLIT_CASES,
    NOT_COMPOUND_CASES,
    CONJUGATED_VERB_TYPE_CASES,
    VERB_LEMMA_CORRECT_CASES,
    MORPHOLOGY_CASES,
    SEPARABLE_VERB_FROM_VERB_CASES,
    SEPARABLE_VERB_FROM_PREFIX_CASES,
    MODAL_INFINITIVE_CASES,
    ZU_INFINITIVE_NOT_SEPARABLE_CASES,
    COMPOUND_TENSE_CASES,
    PLURAL_NOUN_CASES,
    SINGULAR_NOUN_CASES,
    LASSEN_FROM_LASSEN_CASES,
)

ACCURACY_THRESHOLD = 0.90


def run_case(label, fn):
    """Run a single case, return (passed: bool, message: str)."""
    try:
        fn()
        return True, None
    except AssertionError as e:
        return False, f"  FAIL [{label}] {e}"
    except Exception as e:
        return False, f"  ERROR [{label}] {type(e).__name__}: {e}"


def collect_results(cases):
    passed, failed = 0, []
    for label, fn in cases:
        ok, msg = run_case(label, fn)
        if ok:
            passed += 1
        else:
            failed.append(msg)
    return passed, failed


def test_overall_accuracy():
    all_cases = []

    # Compound splits
    for word, expected in COMPOUND_SPLIT_CASES:
        def fn(w=word, e=expected):
            parts = split_compound(w)
            assert parts is not None, f"'{w}' should split"
            assert [p.lower() for p in parts] == [p.lower() for p in e], \
                f"got {parts}, expected {e}"
        all_cases.append((f"compound_split:{word}", fn))

    # Not-compound (derived words)
    for word in NOT_COMPOUND_CASES:
        def fn(w=word):
            parts = split_compound(w)
            assert parts is None, f"'{w}' is derived, should not split (got {parts})"
        all_cases.append((f"not_compound:{word}", fn))

    # Conjugated verb type
    for word, context in CONJUGATED_VERB_TYPE_CASES:
        def fn(w=word, ctx=context):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.word_type == "conjugated_verb", \
                f"expected 'conjugated_verb', got '{r.word_type}'"
        all_cases.append((f"verb_type:{word}", fn))

    # Verb lemmas
    for word, context, expected_lemma in VERB_LEMMA_CORRECT_CASES:
        def fn(w=word, ctx=context, el=expected_lemma):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.lemma == el, f"expected lemma '{el}', got '{r.lemma}'"
        all_cases.append((f"verb_lemma:{word}", fn))

    # Morphology
    for word, context, expected_morph in MORPHOLOGY_CASES:
        def fn(w=word, ctx=context, em=expected_morph):
            r = analyze_word(w, context=ctx, source_lang="de")
            for key, val in em.items():
                assert r.morph.get(key) == val, \
                    f"morph['{key}'] expected '{val}', got '{r.morph.get(key)}'"
        all_cases.append((f"morphology:{word}", fn))

    # Separable verbs from verb
    for word, context, expected_inf in SEPARABLE_VERB_FROM_VERB_CASES:
        def fn(w=word, ctx=context, ei=expected_inf):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.lang_analysis is not None, "no lang_analysis"
            assert r.lang_analysis.lemma == ei, \
                f"expected infinitive '{ei}', got '{r.lang_analysis.lemma}'"
        all_cases.append((f"separable_verb:{word}", fn))

    # Separable verbs from prefix
    for word, context, expected_inf in SEPARABLE_VERB_FROM_PREFIX_CASES:
        def fn(w=word, ctx=context, ei=expected_inf):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.word_type == "separable_prefix", \
                f"expected 'separable_prefix', got '{r.word_type}'"
            assert r.lang_analysis is not None
            assert r.lang_analysis.lemma == ei, \
                f"expected infinitive '{ei}', got '{r.lang_analysis.lemma}'"
        all_cases.append((f"separable_prefix:{word}", fn))

    # Modal infinitive
    for word, context in MODAL_INFINITIVE_CASES:
        def fn(w=word, ctx=context):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.word_type == "conjugated_verb", \
                f"expected 'conjugated_verb', got '{r.word_type}'"
        all_cases.append((f"modal_inf:{word}", fn))

    # Zu-infinitive not separable
    for word, context in ZU_INFINITIVE_NOT_SEPARABLE_CASES:
        def fn(w=word, ctx=context):
            r = analyze_word(w, context=ctx, source_lang="de")
            if r.lang_analysis and r.lang_analysis.lemma:
                assert not r.lang_analysis.lemma.startswith("zu"), \
                    f"should not detect as 'zu{w}', got '{r.lang_analysis.lemma}'"
        all_cases.append((f"zu_inf:{word}", fn))

    # Compound tenses
    for word, context, tense_hint in COMPOUND_TENSE_CASES:
        def fn(w=word, ctx=context, th=tense_hint):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.word_type == "conjugated_verb", \
                f"expected 'conjugated_verb', got '{r.word_type}'"
            assert r.lang_analysis is not None
            assert r.lang_analysis.breakdown_fn is not None
            breakdown = r.lang_analysis.breakdown_fn(r, "test")
            assert th.lower() in breakdown.lower(), \
                f"breakdown should mention '{th}', got: {breakdown}"
        all_cases.append((f"compound_tense:{word}({tense_hint})", fn))

    # Plural nouns
    for word, context, expected_lemma in PLURAL_NOUN_CASES:
        def fn(w=word, ctx=context, el=expected_lemma):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.word_type == "plural_noun", \
                f"expected 'plural_noun', got '{r.word_type}'"
            assert r.lemma == el, f"expected lemma '{el}', got '{r.lemma}'"
        all_cases.append((f"plural_noun:{word}", fn))

    # Singular nouns
    for word, context, expected_gender in SINGULAR_NOUN_CASES:
        def fn(w=word, ctx=context, eg=expected_gender):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.word_type == "noun", \
                f"expected 'noun', got '{r.word_type}'"
            assert r.morph.get("Gender") == eg, \
                f"expected gender '{eg}', got '{r.morph.get('Gender')}'"
        all_cases.append((f"singular_noun:{word}", fn))

    # Lassen constructions
    for word, context, expected_canonical in LASSEN_FROM_LASSEN_CASES:
        def fn(w=word, ctx=context, ec=expected_canonical):
            r = analyze_word(w, context=ctx, source_lang="de")
            assert r.lang_analysis is not None, "no lang_analysis"
            assert r.lang_analysis.lemma == ec, \
                f"expected canonical '{ec}', got '{r.lang_analysis.lemma}'"
        all_cases.append((f"lassen:{word}", fn))

    # ── Run all ──────────────────────────────────────────────────────────────
    passed, failures = collect_results(all_cases)
    total = len(all_cases)
    accuracy = passed / total

    # Always print the report
    print(f"\n{'─' * 60}")
    print(f"  Accuracy: {passed}/{total} ({accuracy:.1%})")
    print(f"  Threshold: {ACCURACY_THRESHOLD:.0%}")
    print(f"{'─' * 60}")
    if failures:
        print(f"\n  Failing cases ({len(failures)}):")
        for msg in failures:
            print(msg)
    print()

    assert accuracy >= ACCURACY_THRESHOLD, (
        f"Accuracy {accuracy:.1%} is below the {ACCURACY_THRESHOLD:.0%} threshold "
        f"({total - passed}/{total} cases failed)"
    )
