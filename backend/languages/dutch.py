"""Dutch language configuration."""

from languages.base import LanguageConfig, LanguageModule


class Dutch(LanguageModule):
    """Dutch language support."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="nl",
            name="Dutch",
            spacy_model="nl_core_news_sm",
        )
