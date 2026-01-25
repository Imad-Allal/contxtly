"""English language configuration."""

from languages.base import LanguageConfig, LanguageModule


class English(LanguageModule):
    """English language support."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="en",
            name="English",
            spacy_model="en_core_web_sm",
        )
