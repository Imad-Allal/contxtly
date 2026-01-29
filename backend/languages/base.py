from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# Universal morphology labels (based on Universal Dependencies)
# (Work across all languages supported by spaCy)
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

    # Compound word settings (only needed for languages with compounds like German)
    supports_compounds: bool = False
    compound_min_length: int = 10
    compound_prefixes: set[str] = field(default_factory=set)
    compound_linking_patterns: list[tuple[str, str]] = field(default_factory=list)



class LanguageModule(ABC):
    """Abstract base class for language modules."""

    @property
    @abstractmethod
    def config(self) -> LanguageConfig:
        """Return the language configuration."""
        pass

    def clean_compound_part(self, part: str) -> str:
        """Remove linking elements from compound parts. Override for language-specific logic."""
        if not self.config.compound_linking_patterns:
            return part

        part_lower = part.lower()
        for link, base in self.config.compound_linking_patterns:
            if part_lower.endswith(link) and len(part) > len(link) + 2:
                return part[:-len(link)] + base
        return part

    def should_split_compound(self, word: str) -> bool:
        """Check if a word should be considered for compound splitting."""
        return (
            self.config.supports_compounds
            and len(word) >= self.config.compound_min_length
        )

    def is_compound_prefix(self, part: str) -> bool:
        """Check if a part is a prefix that shouldn't be split."""
        if not self.config.compound_prefixes:
            return False
        return part.lower() in self.config.compound_prefixes

    def classify_noun(self, token, morph: dict[str, str]) -> str:
        """Classify a noun. Override for language-specific logic."""
        if self.should_split_compound(token.text):
            return "compound_noun"
        if morph.get("Number") == "Plur":
            return "plural_noun"
        return "simple"

    def classify_adjective(self, token, morph: dict[str, str]) -> str:
        """Classify an adjective. Override for language-specific logic."""
        if self.should_split_compound(token.text):
            return "compound_adjective"
        return "simple"
