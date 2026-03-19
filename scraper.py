import requests
from bs4 import BeautifulSoup


def extract_site_content(url: str) -> str:
    """Extrai texto visível de uma URL, removendo scripts, styles e navegação."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remover elementos de ruído
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Limpar linhas vazias excessivas
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)
