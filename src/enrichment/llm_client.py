"""LLM client for section classification enrichment."""

import structlog

from config.settings import Settings
from src.models.visa import CANONICAL_SECTION_TYPES

logger = structlog.get_logger()


class LLMClient:
    """Unified LLM client for visa section classification.

    Supports Anthropic Claude, OpenAI, and Azure OpenAI models for classifying
    visa sections into canonical types.
    """

    def __init__(self, settings: Settings):
        """Initialize LLM client.

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Initialize appropriate client based on provider
        if settings.LLM_PROVIDER == "anthropic":
            import anthropic

            self.client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
            self.provider = "anthropic"
        elif settings.LLM_PROVIDER == "openai":
            import openai

            self.client = openai.OpenAI(api_key=settings.LLM_API_KEY)
            self.provider = "openai"
        elif settings.LLM_PROVIDER == "azure":
            import openai

            self.client = openai.OpenAI(
                base_url=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.LLM_API_KEY,
            )
            self.provider = "azure"
        else:
            raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")

        logger.info("llm_client_initialized", provider=self.provider, model=settings.LLM_MODEL)

    async def classify_section(self, title: str, content: str) -> str:
        """Classify a visa section into a canonical type.

        This uses zero-temperature LLM inference to deterministically
        classify sections. The LLM never modifies content, only classifies.

        Args:
            title: Section title
            content: Section content (first 300 chars used)

        Returns:
            Section type from CANONICAL_SECTION_TYPES
        """
        # Truncate content for prompt
        content_preview = content[:300] if len(content) > 300 else content

        prompt = self._build_classification_prompt(title, content_preview)

        try:
            if self.provider == "anthropic":
                section_type = await self._classify_anthropic(prompt)
            else:  # openai or azure
                section_type = await self._classify_openai(prompt)

            # Validate against canonical enum
            if section_type not in CANONICAL_SECTION_TYPES:
                logger.warning(
                    "invalid_section_type",
                    title=title,
                    llm_response=section_type,
                    defaulting_to="other",
                )
                section_type = "other"

            logger.debug("section_classified", title=title, section_type=section_type)

            return section_type

        except Exception as e:
            logger.error("classification_failed", title=title, error=str(e))
            return "other"

    async def _classify_anthropic(self, prompt: str) -> str:
        """Classify using Anthropic Claude.

        Args:
            prompt: Classification prompt

        Returns:
            Section type
        """
        response = self.client.messages.create(
            model=self.settings.LLM_MODEL,
            max_tokens=50,
            temperature=self.settings.LLM_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )

        section_type = response.content[0].text.strip().lower()
        return section_type

    async def _classify_openai(self, prompt: str) -> str:
        """Classify using OpenAI or Azure OpenAI.

        Args:
            prompt: Classification prompt

        Returns:
            Section type
        """
        # For Azure, use deployment name; for OpenAI, use model name
        model_name = (
            self.settings.AZURE_OPENAI_DEPLOYMENT
            if self.provider == "azure"
            else self.settings.LLM_MODEL
        )

        response = self.client.chat.completions.create(
            model=model_name,
            temperature=self.settings.LLM_TEMPERATURE,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )

        section_type = response.choices[0].message.content.strip().lower()
        return section_type

    def _build_classification_prompt(self, title: str, content_preview: str) -> str:
        """Build zero-temperature classification prompt.

        Args:
            title: Section title
            content_preview: Preview of section content

        Returns:
            Classification prompt
        """
        canonical_types = ", ".join(CANONICAL_SECTION_TYPES)

        return f"""Classify this visa information section into exactly ONE of these types:
{canonical_types}

Section Title: {title}
Content Preview: {content_preview}...

Rules:
- Output ONLY the section type (one word), nothing else
- If unsure, output "other"
- Do not rewrite or infer anything
- Do not add explanations
- Temperature is 0 for deterministic output

Section Type:"""
