"""Descoberta de URLs de um site via sitemap.xml ou crawling de links internos."""

import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from defusedxml.ElementTree import fromstring, ParseError as XMLParseError

import config

logger = logging.getLogger("kipiai.sitemap")

# Padrões de URL a excluir por padrão
_EXCLUDE_PATTERNS = [
    "/blog/", "/tag/", "/category/", "/author/", "/page/",
    "/feed", "/wp-json", "/wp-admin", "/wp-login",
    ".pdf", ".jpg", ".png", ".gif", ".svg", ".css", ".js",
    "/cart", "/checkout", "/my-account", "/login", "/register",
]


def _normalize_url(url: str) -> str:
    """Remove fragmento e trailing slash para deduplicação."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _is_same_domain(url: str, base_domain: str) -> bool:
    """Verifica se a URL pertence ao mesmo domínio base."""
    try:
        return urlparse(url).netloc.replace("www.", "") == base_domain.replace("www.", "")
    except (ValueError, AttributeError):
        return False


def _should_exclude(url: str, exclude_patterns: list[str] | None = None) -> bool:
    """Verifica se a URL deve ser excluída."""
    patterns = exclude_patterns or _EXCLUDE_PATTERNS
    url_lower = url.lower()
    return any(p in url_lower for p in patterns)


def _parse_sitemap_xml(content: str, base_domain: str, max_pages: int, _depth: int = 0) -> list[dict]:
    """Parseia um sitemap.xml e retorna lista de URLs (max depth 3)."""
    if _depth > 3:
        logger.warning("Sitemap recursion depth limit (3) atingido")
        return []
    urls = []
    try:
        root = fromstring(content)
    except (XMLParseError, Exception):
        return []

    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # Verifica se é sitemap index
    sitemap_tags = root.findall(f"{ns}sitemap")
    if sitemap_tags:
        for sitemap_tag in sitemap_tags:
            if len(urls) >= max_pages:
                break
            loc = sitemap_tag.find(f"{ns}loc")
            if loc is not None and loc.text:
                try:
                    resp = requests.get(loc.text.strip(), headers=config.SCRAPER_HEADERS, timeout=15)
                    resp.raise_for_status()
                    child_urls = _parse_sitemap_xml(resp.text, base_domain, max_pages - len(urls), _depth + 1)
                    urls.extend(child_urls)
                except (requests.RequestException, XMLParseError) as e:
                    logger.debug("Falha ao buscar sitemap child %s: %s", loc.text, e)
                    continue
        return urls[:max_pages]

    # Sitemap normal
    for url_tag in root.findall(f"{ns}url"):
        if len(urls) >= max_pages:
            break
        loc = url_tag.find(f"{ns}loc")
        if loc is None or not loc.text:
            continue
        url = loc.text.strip()
        if not _is_same_domain(url, base_domain):
            continue
        if _should_exclude(url):
            continue

        lastmod_tag = url_tag.find(f"{ns}lastmod")
        lastmod = lastmod_tag.text.strip() if lastmod_tag is not None and lastmod_tag.text else ""

        urls.append({
            "url": _normalize_url(url),
            "lastmod": lastmod,
            "source": "sitemap",
        })

    return urls[:max_pages]


def _discover_from_sitemap(base_url: str, base_domain: str, max_pages: int) -> list[dict]:
    """Tenta descobrir URLs via robots.txt → sitemap.xml."""
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    sitemap_urls_to_try = []

    # Tenta robots.txt primeiro
    try:
        robots_url = f"{origin}/robots.txt"
        resp = requests.get(robots_url, headers=config.SCRAPER_HEADERS, timeout=10)
        if resp.status_code == 200:
            for line in resp.text.splitlines():
                if line.strip().lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    if ":" in sitemap_url:
                        sitemap_urls_to_try.append(sitemap_url)
    except requests.RequestException:
        pass

    # Fallback: tenta URLs comuns de sitemap
    if not sitemap_urls_to_try:
        sitemap_urls_to_try = [
            f"{origin}/sitemap.xml",
            f"{origin}/sitemap_index.xml",
            f"{origin}/wp-sitemap.xml",
        ]

    for sitemap_url in sitemap_urls_to_try:
        try:
            resp = requests.get(sitemap_url, headers=config.SCRAPER_HEADERS, timeout=15)
            if resp.status_code == 200 and "xml" in resp.headers.get("content-type", "").lower():
                urls = _parse_sitemap_xml(resp.text, base_domain, max_pages)
                if urls:
                    return urls
            # Tenta parsear mesmo sem content-type xml
            if resp.status_code == 200 and "<urlset" in resp.text[:500]:
                urls = _parse_sitemap_xml(resp.text, base_domain, max_pages)
                if urls:
                    return urls
        except (requests.RequestException, XMLParseError) as e:
            logger.debug("Falha ao buscar sitemap %s: %s", sitemap_url, e)
            continue

    return []


def _discover_from_links(base_url: str, base_domain: str, max_pages: int) -> list[dict]:
    """Fallback: extrai links internos do homepage (profundidade 1)."""
    urls = []
    seen = set()

    try:
        resp = requests.get(base_url, headers=config.SCRAPER_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Adiciona a própria homepage
    normalized_base = _normalize_url(base_url)
    seen.add(normalized_base)
    urls.append({"url": normalized_base, "lastmod": "", "source": "homepage"})

    for a_tag in soup.find_all("a", href=True):
        if len(urls) >= max_pages:
            break

        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue

        full_url = urljoin(base_url, href)
        normalized = _normalize_url(full_url)

        if normalized in seen:
            continue
        if not _is_same_domain(full_url, base_domain):
            continue
        if _should_exclude(full_url):
            continue

        seen.add(normalized)
        urls.append({"url": normalized, "lastmod": "", "source": "link"})

    return urls[:max_pages]


def discover_urls(base_url: str, max_pages: int = 50) -> list[dict]:
    """Descobre URLs de um site via sitemap.xml ou crawling de links.

    Retorna lista de dicts com {url, lastmod, source}.
    source pode ser: "sitemap", "link", "homepage".
    """
    base_domain = urlparse(base_url).netloc

    # Tenta sitemap primeiro
    urls = _discover_from_sitemap(base_url, base_domain, max_pages)

    if urls:
        # Garante que a homepage está incluída
        normalized_base = _normalize_url(base_url)
        if not any(u["url"] == normalized_base for u in urls):
            urls.insert(0, {"url": normalized_base, "lastmod": "", "source": "homepage"})
            urls = urls[:max_pages]
        return urls

    # Fallback: crawling de links
    return _discover_from_links(base_url, base_domain, max_pages)
