"""Request model for concept suggest endpoint."""

from pydantic import BaseModel, Field, field_validator
import langcodes

# Supported language codes (ISO 639-1)
SUPPORTED_LANGUAGES = {
    "en",  # English
    "de",  # German
    "es",  # Spanish
    "fr",  # French
    "pt",  # Portuguese
    "it",  # Italian
    "da",  # Danish
}


class SuggestRequest(BaseModel):
    """
    Request model for /api/v1/concepts/suggest/ endpoint.

    This endpoint provides concept suggestions based on a search query.

    Supported languages: English (en), German (de), Spanish (es), French (fr),
    Portuguese (pt), Italian (it), Danish (da)

    Example:
        >>> request = SuggestRequest(query="carbon", language="en")
        >>> params = request.to_query_params()
        >>> # {'query': 'carbon', 'language': 'en'}
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query string for concept suggestions"
    )

    language: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="ISO 639-1 language code (en, de, es, fr, pt, it, da)"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and clean the query string."""
        # Strip whitespace
        v = v.strip()

        if not v:
            raise ValueError("Query cannot be empty or only whitespace")

        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code against supported languages."""
        # Convert to lowercase
        v = v.lower().strip()

        if not v:
            raise ValueError("Language code is required")

        # Validate it's a valid ISO 639-1 language code
        if not langcodes.tag_is_valid(v):
            raise ValueError(f"Invalid language code: {v}")

        # Check if it's in our supported list
        if v not in SUPPORTED_LANGUAGES:
            supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
            raise ValueError(
                f"Language '{v}' is not supported. "
                f"Supported languages: {supported}"
            )

        return v

    def to_query_params(self) -> dict[str, str]:
        """
        Convert request model to query parameters dictionary.

        Returns:
            Dictionary of query parameters ready for URL encoding
        """
        return {
            "query": self.query,
            "language": self.language
        }

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "carbon",
                    "language": "en"
                },
                {
                    "query": "sustainability",
                    "language": "de"
                }
            ]
        }
    }
