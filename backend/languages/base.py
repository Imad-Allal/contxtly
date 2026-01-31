from abc import ABC, abstractmethod
from dataclasses import dataclass


# Universal morphology labels (based on Universal Dependencies)
UNIVERSAL_MORPH_LABELS = {
    # Tense
    "Tense=Past": "past tense",
    "Tense=Pres": "present tense",
    "Tense=Fut": "future tense",
    "Tense=Imp": "imperfect",
    "Tense=Pqp": "pluperfect",

    # Person
    "Person=1": "1st person",
    "Person=2": "2nd person",
    "Person=3": "3rd person",

    # Number
    "Number=Sing": "singular",
    "Number=Plur": "plural",

    # Mood
    "Mood=Ind": "indicative",
    "Mood=Sub": "subjunctive",
    "Mood=Imp": "imperative",
    "Mood=Cnd": "conditional",

    # VerbForm
    "VerbForm=Fin": "finite",
    "VerbForm=Inf": "infinitive",
    "VerbForm=Part": "participle",
    "VerbForm=Ger": "gerund",

    # Aspect
    "Aspect=Perf": "perfective",
    "Aspect=Imp": "imperfective",

    # Case (for nouns)
    "Case=Nom": "nominative",
    "Case=Acc": "accusative",
    "Case=Dat": "dative",
    "Case=Gen": "genitive",

    # Gender
    "Gender=Masc": "masculine",
    "Gender=Fem": "feminine",
    "Gender=Neut": "neuter",

    # Degree (for adjectives)
    "Degree=Pos": "positive",
    "Degree=Cmp": "comparative",
    "Degree=Sup": "superlative",
}


def describe_morphology(morph_dict: dict[str, str], include: list[str] | None = None) -> str:
    """
    Convert spaCy morphology dict to human-readable description.

    Args:
        morph_dict: Dict from token.morph.to_dict()
        include: Optional list of features to include (e.g., ["Tense", "Person", "Number"])
                 If None, includes all recognized features.

    Returns:
        Human-readable description like "present tense, 3rd person, singular"
    """
    descriptions = []

    for key, value in morph_dict.items():
        if include and key not in include:
            continue

        label = f"{key}={value}"
        if label in UNIVERSAL_MORPH_LABELS:
            descriptions.append(UNIVERSAL_MORPH_LABELS[label])

    return ", ".join(descriptions) if descriptions else ""


@dataclass
class LanguageConfig:
    """Configuration for a specific language."""

    code: str  # ISO 639-1 code (e.g., "de", "fr")
    name: str  # Display name (e.g., "German", "French")
    spacy_model: str  # spaCy model name


class LanguageModule(ABC):
    """Abstract base class for language modules."""

    @property
    @abstractmethod
    def config(self) -> LanguageConfig:
        """Return the language configuration."""
        pass

    def classify_noun(self, token, morph: dict[str, str]) -> str:
        """Classify a noun. Override for language-specific logic."""
        if morph.get("Number") == "Plur":
            return "plural_noun"
        return "simple"

    def split_compound(self, word: str) -> list[str] | None:
        """Split a compound word. Override for language-specific logic."""
        return None
