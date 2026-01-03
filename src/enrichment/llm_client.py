"""LLM client for section classification enrichment and generic content extraction."""

import json
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

        # Use max_completion_tokens for newer models (GPT-4o, GPT-5, etc.)
        response = self.client.chat.completions.create(
            model=model_name,
            temperature=self.settings.LLM_TEMPERATURE,
            max_completion_tokens=50,
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

    async def extract_structured_data(self, page_title: str, content: str) -> dict:
        """Extract structured data from a page using LLM.

        Args:
            page_title: Title of the page
            content: Page content (text)

        Returns:
            Dict with extracted structured data
        """
        prompt = self._build_extraction_prompt(page_title, content)

        try:
            if self.provider == "anthropic":
                result = await self._extract_anthropic(prompt)
            else:  # openai or azure
                result = await self._extract_openai(prompt)

            logger.info("content_extracted", title=page_title, fields=len(result.get("structured_data", {})))
            return result

        except Exception as e:
            logger.error("extraction_failed", title=page_title, error=str(e))
            return {
                "content_type": "unknown",
                "summary": "",
                "structured_data": {}
            }

    async def synthesize_pages(self, pages_data: list) -> dict:
        """Synthesize multiple pages into a cohesive structure.

        Args:
            pages_data: List of extracted page data dicts

        Returns:
            Dict with synthesized structured data
        """
        prompt = self._build_synthesis_prompt(pages_data)

        try:
            if self.provider == "anthropic":
                result = await self._synthesize_anthropic(prompt)
            else:  # openai or azure
                result = await self._synthesize_openai(prompt)

            logger.info("pages_synthesized", num_pages=len(pages_data))
            return result

        except Exception as e:
            logger.error("synthesis_failed", num_pages=len(pages_data), error=str(e))
            return {}

    async def _extract_anthropic(self, prompt: str) -> dict:
        """Extract using Anthropic Claude.

        Args:
            prompt: Extraction prompt

        Returns:
            Extracted data as dict
        """
        response = self.client.messages.create(
            model=self.settings.LLM_MODEL,
            max_tokens=4000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        return self._parse_json_response(text)

    async def _extract_openai(self, prompt: str) -> dict:
        """Extract using OpenAI or Azure OpenAI.

        Args:
            prompt: Extraction prompt

        Returns:
            Extracted data as dict
        """
        model_name = (
            self.settings.AZURE_OPENAI_DEPLOYMENT
            if self.provider == "azure"
            else self.settings.LLM_MODEL
        )

        # Use max_completion_tokens for newer models (GPT-4o, GPT-5, etc.)
        # GPT-5.x models don't support custom temperature, only default (1)
        response = self.client.chat.completions.create(
            model=model_name,
            # temperature=0.3,  # Disabled for GPT-5.x compatibility
            max_completion_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.choices[0].message.content.strip()
        return self._parse_json_response(text)

    async def _synthesize_anthropic(self, prompt: str) -> dict:
        """Synthesize using Anthropic Claude.

        Args:
            prompt: Synthesis prompt

        Returns:
            Synthesized data as dict
        """
        response = self.client.messages.create(
            model=self.settings.LLM_MODEL,
            max_tokens=8000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        return self._parse_json_response(text)

    async def _synthesize_openai(self, prompt: str) -> dict:
        """Synthesize using OpenAI or Azure OpenAI.

        Args:
            prompt: Synthesis prompt

        Returns:
            Synthesized data as dict
        """
        model_name = (
            self.settings.AZURE_OPENAI_DEPLOYMENT
            if self.provider == "azure"
            else self.settings.LLM_MODEL
        )

        # Use max_completion_tokens for newer models (GPT-4o, GPT-5, etc.)
        # GPT-5.x models don't support custom temperature, only default (1)
        response = self.client.chat.completions.create(
            model=model_name,
            # temperature=0.3,  # Disabled for GPT-5.x compatibility
            max_completion_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.choices[0].message.content.strip()
        return self._parse_json_response(text)

    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from LLM response.

        Args:
            text: Raw LLM response

        Returns:
            Parsed JSON dict
        """
        # Try to extract JSON from markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_str = text[start:end].strip()
        else:
            json_str = text

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning("json_parse_failed", error=str(e), text_preview=text[:200])
            return {}

    def _build_extraction_prompt(self, page_title: str, content: str) -> str:
        """Build prompt for extracting structured data from a page.

        Args:
            page_title: Page title
            content: Page content

        Returns:
            Extraction prompt
        """
        # Limit content length to avoid token limits
        max_content = 6000
        if len(content) > max_content:
            content = content[:max_content] + "\n...(content truncated)..."

        return f"""You are a web content analyzer. Extract structured information from this webpage.

**Page Title:** {page_title}

**Content:**
{content}

**Task:**
1. Identify the content type (e.g., "visa_information", "processing_times", "course_details", "requirements", "general_information", etc.)
2. Write a brief summary (2-3 sentences)
3. Extract key structured data that would be useful (be intelligent about what makes sense for this content type)

**Output Format (JSON):**
```json
{{
  "content_type": "the type of content",
  "summary": "brief summary of the page",
  "structured_data": {{
    // Extract relevant fields based on content
    // For visa info: requirements, eligibility, costs, processing times, etc.
    // For courses: course_name, duration, fees, entry_requirements, etc.
    // For processing times: visa_types and their processing times
    // Be creative and intelligent about what makes sense
  }}
}}
```

**Important:**
- Extract only factual information present in the content
- Use clear, consistent field names
- Include units for numbers (e.g., "24 months", "$7,000 AUD")
- Return ONLY the JSON, no other text

JSON Output:"""

    def _build_synthesis_prompt(self, pages_data: list) -> str:
        """Build prompt for synthesizing multiple pages.

        Args:
            pages_data: List of extracted page data

        Returns:
            Synthesis prompt
        """
        # Format pages data for the prompt
        pages_summary = []
        for i, page in enumerate(pages_data, 1):
            pages_summary.append(f"""
Page {i}:
- URL: {page.get('url', 'unknown')}
- Title: {page.get('title', 'unknown')}
- Content Type: {page.get('content_type', 'unknown')}
- Summary: {page.get('summary', '')}
- Structured Data: {json.dumps(page.get('structured_data', {}), indent=2)}
""")

        pages_text = "\n".join(pages_summary)

        return f"""You are a content synthesizer. You have data extracted from {len(pages_data)} related webpages.

**Your task:**
Combine all this information into ONE cohesive, well-organized JSON structure that:
1. Removes duplicates
2. Organizes related information together
3. Creates a logical hierarchy
4. Maintains all important details
5. Makes the data easy to understand and use

**Extracted Pages:**
{pages_text}

**Output Format:**
Return a JSON object that intelligently combines all this information. The structure should make sense for the content type.

For example:
- If these are different visa types, organize by visa category
- If these are processing times, create a structured table/list
- If these are course pages, organize by course type or faculty
- Be creative and logical based on the actual content

**Important:**
- Create a clear, logical structure
- Don't lose important information
- Remove redundancy
- Use consistent naming
- Return ONLY the JSON, no other text

JSON Output:"""
