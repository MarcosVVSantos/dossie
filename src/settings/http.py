from __future__ import annotations
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional


def create_session(retries: int = 3, backoff_factor: float = 0.3, status_forcelist=(500, 502, 504), timeout: Optional[int] = None) -> requests.Session:
    """Cria uma sessão requests com política de retry configurada.

    - retries: número de tentativas
    - backoff_factor: fator exponencial
    - status_forcelist: códigos que disparam retry
    - timeout: tempo padrão (não aplicado automaticamente; usar `.request` wrapper se necessário)
    """
    session = requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist, raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # attach default timeout info for convenience
    session.request_timeout = timeout
    return session


def request_with_timeout(session: requests.Session, method: str, url: str, timeout: Optional[int] = None, **kwargs):
    """Convenience wrapper to use session with a default timeout if provided."""
    to = timeout if timeout is not None else getattr(session, "request_timeout", None) or 30
    return session.request(method, url, timeout=to, **kwargs)
