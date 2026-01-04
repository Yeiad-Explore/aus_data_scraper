"""Generic content data enricher using LLM classification."""

import structlog

from src.enrichment.llm_client import LLMClient
from src.models.visa import EnrichedContentData, EnrichedContentSection, ContentData

logger = structlog.get_logger()


class ContentEnricher:
    """Post-processes parsed content JSON with LLM section classification.

    This enricher takes clean parsed JSON (ground truth) and adds
    semantic classification to sections using an LLM. The LLM never
    modifies content, only classifies sections into canonical types.
    """

    def __init__(self, llm_client: LLMClient):
        """Initialize enricher.

        Args:
            llm_client: LLM client for classification
        """
        self.llm = llm_client

    async def enrich(self, content: ContentData) -> EnrichedContentData:
        """Enrich content data by classifying all sections.

        Args:
            content: Clean content data from parser

        Returns:
            Enriched content data with classified sections
        """
        logger.info("enriching_content", title=content.title, sections=len(content.sections))

        enriched_sections = []

        for section in content.sections:
            # Classify section using LLM
            section_type = await self.llm.classify_section(section.title, section.content)

            # Create enriched section
            enriched_section = EnrichedContentSection(
                title=section.title, content=section.content, section_type=section_type
            )

            enriched_sections.append(enriched_section)

        # Create enriched content data
        enriched = EnrichedContentData(
            title=content.title,
            category=content.category,
            summary=content.summary,
            sections=enriched_sections,
            source_url=content.source_url,
            scraped_at=content.scraped_at,
        )

        # Count section types for logging
        section_type_counts = {}
        for section in enriched_sections:
            section_type_counts[section.section_type] = (
                section_type_counts.get(section.section_type, 0) + 1
            )

        logger.info(
            "content_enriched",
            title=content.title,
            section_types=section_type_counts,
        )

        return enriched
