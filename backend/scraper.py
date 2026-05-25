"""Fetch a URL and extract security-relevant HTML features for ML inference."""

from dataclasses import asdict, dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; CybersecScanner/1.0; +https://localhost/security-scan)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@dataclass
class ScrapeFeatures:
    url: str
    final_url: str
    status_code: int
    form_count: int
    iframe_count: int
    hidden_iframe_count: int
    has_password_field: bool
    password_input_count: int
    hidden_input_count: int
    external_link_count: int
    script_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def _is_hidden_iframe(iframe: Tag) -> bool:
    if iframe.has_attr("hidden"):
        return True

    style = (iframe.get("style") or "").replace(" ", "").lower()
    if "display:none" in style or "visibility:hidden" in style:
        return True

    width = (iframe.get("width") or "").strip().lower()
    height = (iframe.get("height") or "").strip().lower()
    if width in {"0", "0px"} or height in {"0", "0px"}:
        return True

    return False


def _parse_html(url: str, final_url: str, status_code: int, html: str) -> ScrapeFeatures:
    soup = BeautifulSoup(html, "html.parser")
    base_host = urlparse(final_url).netloc.lower()

    forms = soup.find_all("form")
    iframes = soup.find_all("iframe")
    hidden_iframes = [iframe for iframe in iframes if _is_hidden_iframe(iframe)]

    password_inputs = soup.find_all("input", attrs={"type": "password"})
    hidden_inputs = soup.find_all("input", attrs={"type": "hidden"})

    external_links = 0
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urljoin(final_url, href)
        link_host = urlparse(absolute).netloc.lower()
        if link_host and link_host != base_host:
            external_links += 1

    return ScrapeFeatures(
        url=url,
        final_url=final_url,
        status_code=status_code,
        form_count=len(forms),
        iframe_count=len(iframes),
        hidden_iframe_count=len(hidden_iframes),
        has_password_field=len(password_inputs) > 0,
        password_input_count=len(password_inputs),
        hidden_input_count=len(hidden_inputs),
        external_link_count=external_links,
        script_count=len(soup.find_all("script")),
    )


async def scrape_url(url: str, timeout: float = 15.0) -> ScrapeFeatures:
    """Download a page and extract structural features with BeautifulSoup."""
    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=timeout,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    return _parse_html(
        url=url,
        final_url=str(response.url),
        status_code=response.status_code,
        html=response.text,
    )
