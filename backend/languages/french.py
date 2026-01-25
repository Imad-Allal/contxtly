"""French language configuration."""

from languages.base import LanguageConfig, LanguageModule


class French(LanguageModule):
    """French language support."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="fr",
            name="French",
            spacy_model="fr_core_news_sm",
        )
