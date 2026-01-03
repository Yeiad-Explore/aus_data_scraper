"""Visa data enricher using LLM classification."""

import structlog

from src.enrichment.llm_client import LLMClient
from src.models.visa import EnrichedVisaData, EnrichedVisaSection, VisaData

logger = structlog.get_logger()


class VisaEnricher:
    """Post-processes parsed visa JSON with LLM section classification.

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

    async def enrich(self, visa: VisaData) -> EnrichedVisaData:
        """Enrich visa data by classifying all sections.

        Args:
            visa: Clean visa data from parser

        Returns:
            Enriched visa data with classified sections
        """
        logger.info("enriching_visa", visa_name=visa.visa_name, sections=len(visa.sections))

        enriched_sections = []

        for section in visa.sections:
            # Classify section using LLM
            section_type = await self.llm.classify_section(section.title, section.content)

            # Create enriched section
            enriched_section = EnrichedVisaSection(
                title=section.title, content=section.content, section_type=section_type
            )

            enriched_sections.append(enriched_section)

        # Create enriched visa data
        enriched = EnrichedVisaData(
            visa_name=visa.visa_name,
            subclass=visa.subclass,
            category=visa.category,
            summary=visa.summary,
            sections=enriched_sections,
            source_url=visa.source_url,
            scraped_at=visa.scraped_at,
        )

        # Count section types for logging
        section_type_counts = {}
        for section in enriched_sections:
            section_type_counts[section.section_type] = (
                section_type_counts.get(section.section_type, 0) + 1
            )

        logger.info(
            "visa_enriched",
            visa_name=visa.visa_name,
            section_types=section_type_counts,
        )

        return enriched
