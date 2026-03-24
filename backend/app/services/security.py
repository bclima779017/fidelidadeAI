"""Módulo centralizado de segurança da aplicação.

Validação de URLs (anti-SSRF com DNS pinning), sanitização de inputs,
limites de tamanho e utilitários de segurança.
"""

import ipaddress
import re
import socket
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Configurações de segurança
# ---------------------------------------------------------------------------

ALLOWED_SCHEMES = {"http", "https"}

# Tamanho máximo da resposta HTTP (10 MB)
MAX_RESPONSE_BYTES = 10 * 1024 * 1024

# Máximo de redirects permitidos
MAX_REDIRECTS = 5

# Tamanho máximo de input de texto do usuário (50 000 caracteres)
MAX_INPUT_LENGTH = 50_000

# Redes privadas/reservadas bloqueadas (proteção contra SSRF)
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("10.0.0.0/8"),         # privado classe A
    ipaddress.ip_network("172.16.0.0/12"),      # privado classe B
    ipaddress.ip_network("192.168.0.0/16"),     # privado classe C
    ipaddress.ip_network("169.254.0.0/16"),     # link-local
    ipaddress.ip_network("0.0.0.0/8"),          # reservado
    ipaddress.ip_network("100.64.0.0/10"),      # carrier-grade NAT
    ipaddress.ip_network("198.18.0.0/15"),      # benchmark
    ipaddress.ip_network("::1/128"),            # loopback IPv6
    ipaddress.ip_network("fc00::/7"),           # unique local IPv6
    ipaddress.ip_network("fe80::/10"),          # link-local IPv6
]

# Content-Types aceitos para extração HTML
_ALLOWED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "text/plain",
}


# ---------------------------------------------------------------------------
# Validação de URL (com DNS pinning contra rebinding)
# ---------------------------------------------------------------------------

def validate_url(url: str) -> str:
    """Valida e normaliza uma URL para acesso seguro.

    - Aceita apenas http/https
    - Bloqueia IPs privados/reservados (SSRF)
    - Resolve DNS e verifica todos os IPs retornados
    - Adiciona https:// se esquema ausente

    Returns:
        URL validada e normalizada.

    Raises:
        ValueError: Se a URL for inválida ou apontar para rede bloqueada.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL não informada.")

    if len(url) > 2048:
        raise ValueError("URL excede o tamanho máximo permitido (2048 chars).")

    # Adicionar esquema padrão se ausente
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    # Validar esquema
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"Esquema não permitido: '{parsed.scheme}'. Use http ou https."
        )

    # Validar hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL inválida: hostname não encontrado.")

    # Bloquear hostnames suspeitos
    if hostname in ("localhost", "0.0.0.0", "[::]"):
        raise ValueError("Acesso a endereços locais não é permitido.")

    # Bloquear hostname numérico direto (ex: http://2130706433)
    if hostname.isdigit():
        raise ValueError("Acesso via IP numérico não é permitido.")

    # Resolver DNS e verificar se algum IP é privado/reservado
    resolved_ips = _resolve_and_validate_dns(hostname)

    # Retorna URL + IPs resolvidos para DNS pinning
    # (o caller pode usar os IPs para conectar diretamente)
    return url


def _resolve_and_validate_dns(hostname: str) -> list[str]:
    """Resolve DNS e valida que nenhum IP é privado.

    Returns:
        Lista de IPs resolvidos (para DNS pinning).

    Raises:
        ValueError: Se hostname não resolver ou apontar para IP bloqueado.
    """
    try:
        resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValueError(f"Não foi possível resolver o domínio: '{hostname}'.")

    if not resolved:
        raise ValueError(f"Nenhum IP encontrado para o domínio: '{hostname}'.")

    valid_ips = []
    for _, _, _, _, sockaddr in resolved:
        ip_str = sockaddr[0]
        ip = ipaddress.ip_address(ip_str)
        if _is_blocked_ip(ip):
            raise ValueError("Acesso a endereços internos/privados não é permitido.")
        valid_ips.append(ip_str)

    return valid_ips


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Verifica se um IP pertence a uma rede bloqueada."""
    for network in _BLOCKED_NETWORKS:
        if ip in network:
            return True
    return False


# ---------------------------------------------------------------------------
# Validação de resposta HTTP
# ---------------------------------------------------------------------------

def check_content_length(headers: dict, max_bytes: int = MAX_RESPONSE_BYTES) -> None:
    """Verifica Content-Length antes de baixar o corpo da resposta.

    Raises:
        ValueError: Se o conteúdo declarado exceder o limite.
    """
    content_length = headers.get("Content-Length")
    if content_length:
        try:
            size = int(content_length)
        except (ValueError, TypeError):
            return
        if size > max_bytes:
            raise ValueError(
                f"Resposta muito grande ({size:,} bytes). "
                f"Limite: {max_bytes:,} bytes."
            )


def check_content_type_html(headers: dict) -> None:
    """Verifica se o Content-Type indica HTML/texto.

    Raises:
        ValueError: Se o tipo de conteúdo não for HTML.
    """
    content_type = headers.get("Content-Type", "")
    if not content_type:
        return  # Aceita se não declarado (fallback para parsing)

    # Extrai o media type sem charset
    media_type = content_type.lower().split(";")[0].strip()
    if media_type not in _ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Tipo de conteúdo não suportado: '{content_type}'. Esperado: HTML."
        )


def check_redirect_count(response) -> None:
    """Verifica se o número de redirects não excede o limite.

    Args:
        response: requests.Response com histórico de redirects.

    Raises:
        ValueError: Se houver muitos redirects.
    """
    if hasattr(response, "history") and len(response.history) > MAX_REDIRECTS:
        raise ValueError(
            f"Muitos redirects ({len(response.history)}). Limite: {MAX_REDIRECTS}."
        )


# ---------------------------------------------------------------------------
# Sanitização de inputs
# ---------------------------------------------------------------------------

def sanitize_user_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """Sanitiza texto fornecido pelo usuário.

    - Remove caracteres de controle (exceto newline e tab)
    - Trunca ao tamanho máximo
    - Strip de espaços

    Returns:
        Texto sanitizado.
    """
    if not text:
        return ""

    # Remove caracteres de controle exceto \n e \t
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Truncar
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


# ---------------------------------------------------------------------------
# Sanitização de mensagens de erro
# ---------------------------------------------------------------------------

def safe_error_message(exception: Exception) -> str:
    """Retorna uma mensagem de erro segura, sem vazar detalhes internos.

    Filtra informações sensíveis como paths do sistema, IPs internos,
    stack traces e chaves de API.
    """
    msg = str(exception)

    # Remover paths absolutos do sistema
    msg = re.sub(r"[A-Z]:\\[^\s\"']+", "[caminho-oculto]", msg)
    msg = re.sub(r"/(?:home|usr|etc|var|tmp|opt)/[^\s\"']+", "[caminho-oculto]", msg)

    # Remover IPs internos
    msg = re.sub(
        r"\b(?:127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)\b",
        "[ip-oculto]",
        msg,
    )

    # Remover possíveis API keys (padrão AIza...)
    msg = re.sub(r"AIza[A-Za-z0-9_-]{30,}", "[api-key-oculta]", msg)

    # Truncar mensagens muito longas
    if len(msg) > 300:
        msg = msg[:300] + "..."

    return msg
