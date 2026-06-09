"""
Web page scraping and text extraction.
"""

from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.logging import get_logger

logger = get_logger("url_scraper")

MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB HTML max
TIMEOUT_SECONDS = 15.0


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    parsed = urlparse(url)
    return bool(parsed.scheme in ("http", "https") and parsed.netloc)


def _clean_text(text: str) -> str:
    """Collapse whitespace and strip empty lines."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def _extract_article_text(soup: BeautifulSoup) -> Optional[str]:
    """Try to extract main article content using common selectors."""
    selectors = [
        "article",
        "[role='main']",
        "main",
        ".post-content",
        ".entry-content",
        ".content",
        "#content",
    ]

    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return text

    return None


def _strip_unwanted_tags(soup: BeautifulSoup) -> None:
    """Remove script, style, nav, footer, header, aside tags."""
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()


async def scrape_url(url: str) -> Optional[dict]:
    """Scrape a URL and return structured content.

    Args:
        url: The web page URL to scrape.

    Returns:
        Dict with title, text, and url, or None if scraping fails.
    """
    if not is_valid_url(url):
        logger.warning("Invalid URL: %s", url)
        return None

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching %s: %s", url, e.response.status_code)
        return None
    except httpx.RequestError as e:
        logger.error("Request error fetching %s: %s", url, e)
        return None

    content_length = len(response.content)
    if content_length > MAX_CONTENT_LENGTH:
        logger.warning("Content too large: %d bytes", content_length)
        return None

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else url

    # Try article extraction first
    text = _extract_article_text(soup)

    if not text:
        # Fallback: strip unwanted tags and take body text
        _strip_unwanted_tags(soup)
        body = soup.find("body")
        if body:
            text = body.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

    text = _clean_text(text)

    if len(text) < 100:
        logger.warning("Extracted text too short (%d chars) from %s", len(text), url)
        return None

    logger.info("Scraped %d characters from %s", len(text), url)
    return {
        "title": title,
        "text": text,
        "url": url,
        "content_length": content_length,
    }
