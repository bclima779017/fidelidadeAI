import requests
from bs4 import BeautifulSoup
import security

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def extract_site_content(url: str) -> str:
    """Extrai texto visível de uma URL, removendo scripts, styles e navegação."""
    url = security.validate_url(url)
    response = requests.get(
        url, headers=_HEADERS, timeout=30,
        allow_redirects=True, stream=True,
    )
    response.raise_for_status()
    security.check_content_length(response.headers)
    security.check_content_type_html(response.headers)
    content = response.content[:security.MAX_RESPONSE_BYTES]
    response.close()

    soup = BeautifulSoup(content, "html.parser")

    # Remover elementos de ruído
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Limpar linhas vazias excessivas
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _extract_single_page(url: str) -> dict:
    """Extrai conteúdo e título de uma única página.

    Returns:
        Dict com {url, title, content, char_count}.
    """
    url = security.validate_url(url)
    response = requests.get(
        url, headers=_HEADERS, timeout=30,
        allow_redirects=True, stream=True,
    )
    response.raise_for_status()
    security.check_content_length(response.headers)
    security.check_content_type_html(response.headers)
    raw = response.content[:security.MAX_RESPONSE_BYTES]
    response.close()

    soup = BeautifulSoup(raw, "html.parser")

    # Extrai título
    title = ""
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title = title_tag.string.strip()

    # Remover elementos de ruído
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    content = "\n".join(lines)

    return {
        "url": url,
        "title": title,
        "content": content,
        "char_count": len(content),
    }


def extract_multi_page_content(urls: list[str], progress_callback=None) -> list[dict]:
    """Extrai conteúdo de múltiplas URLs.

    Args:
        urls: Lista de URLs para extrair.
        progress_callback: Função(progress: float, text: str) para feedback.

    Returns:
        Lista de dicts {url, title, content, char_count}.
    """
    results = []
    total = len(urls)

    for i, url in enumerate(urls):
        if progress_callback:
            progress_callback(i / total, f"Extraindo {i + 1}/{total}: {url[:60]}...")

        try:
            page = _extract_single_page(url)
            if page["content"].strip():
                results.append(page)
        except Exception as e:
            print(f"  [AVISO] Falha ao extrair {url}: {e}")
            continue

    if progress_callback:
        progress_callback(1.0, f"Extração concluída: {len(results)}/{total} páginas")

    return results
