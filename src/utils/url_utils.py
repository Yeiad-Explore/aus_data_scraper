"""URL utility functions."""

import re
from urllib.parse import urlparse


def url_to_slug(url: str) -> str:
    """Convert URL to filesystem-safe slug.

    This creates a unique, filesystem-safe identifier for each URL.

    Args:
        url: The URL to convert

    Returns:
        Filesystem-safe slug

    Examples:
        >>> url_to_slug("https://example.com/visas/work/visa-482")
        "visas_work_visa_482"
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    # Replace slashes and special characters with underscores
    slug = re.sub(r"[^\w\-]", "_", path)

    # Replace multiple underscores with single underscore
    slug = re.sub(r"_+", "_", slug)

    # Convert to lowercase and strip trailing underscores
    return slug.lower().strip("_")


def is_visa_url(url: str, base_domain: str = "immi.homeaffairs.gov.au") -> bool:
    """Validate URL is within allowed scope.

    Checks that the URL is from the expected domain and under the /visas/ path.

    Args:
        url: The URL to validate
        base_domain: Expected domain (default: immi.homeaffairs.gov.au)

    Returns:
        True if URL is valid, False otherwise

    Examples:
        >>> is_visa_url("https://immi.homeaffairs.gov.au/visas/work/visa-482")
        True
        >>> is_visa_url("https://example.com/visas/work")
        False
        >>> is_visa_url("https://immi.homeaffairs.gov.au/about")
        False
    """
    parsed = urlparse(url)

    # Check domain
    if parsed.netloc != base_domain:
        return False

    # Must be under /visas/
    if not parsed.path.startswith("/visas/"):
        return False

    return True


def normalize_url(url: str, base_url: str) -> str:
    """Convert relative URL to absolute URL.

    Args:
        url: URL to normalize (may be relative or absolute)
        base_url: Base URL to use for relative URLs

    Returns:
        Absolute URL

    Examples:
        >>> normalize_url("/visas/work", "https://immi.homeaffairs.gov.au")
        "https://immi.homeaffairs.gov.au/visas/work"
        >>> normalize_url("https://immi.homeaffairs.gov.au/visas/work", "https://immi.homeaffairs.gov.au")
        "https://immi.homeaffairs.gov.au/visas/work"
    """
    if url.startswith("http://") or url.startswith("https://"):
        return url

    # Remove trailing slash from base_url
    base_url = base_url.rstrip("/")

    # Add leading slash if missing
    if not url.startswith("/"):
        url = "/" + url

    return f"{base_url}{url}"
