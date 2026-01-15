import time
from typing import Optional
import requests

from .config import config
from .http import create_session, request_with_timeout


class Auth:
    """Autenticador que gerencia token com cache e renovação automática."""

    def __init__(self):
        self._token: Optional[str] = None
        self._expiry: Optional[float] = None
        self.session = create_session(retries=2, backoff_factor=0.2)

    def refresh_token(self) -> bool:
        """Obtém novo token de autenticação e atualiza expiry se disponível."""
        auth_url = config.auth_url
        email = config.email
        password = config.password
        client_id = config.client_id
        grant_type = config.grant_type

        if not email or not password:
            print("[AUTH] ❌ email ou password não definidos no config")
            return False

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            'client_id': client_id,
            'grant_type': grant_type,
            'username': email,
            'password': password
        }

        try:
            print("[AUTH] 🔐 Obtendo token...")
            resp = request_with_timeout(self.session, 'POST', auth_url, data=data, headers=headers, timeout=10)
            resp.raise_for_status()
            json_resp = resp.json()
            token = json_resp.get('access_token')
            if not token:
                print(f"[AUTH] ❌ Token não encontrado na resposta: {json_resp}")
                return False

            self._token = token
            expires_in = json_resp.get('expires_in')
            if expires_in:
                self._expiry = time.time() + int(expires_in) - 30  # renova 30s antes
            else:
                self._expiry = None

            print(f"[AUTH] ✅ Token obtido (primeiros 20 chars): {self._token[:20]}...")
            return True

        except requests.exceptions.RequestException as e:
            print(f"[AUTH] ❌ Erro na requisição HTTP: {e}")
            return False
        except ValueError as e:
            print(f"[AUTH] ❌ Erro ao parsear JSON: {e}")
            return False
        except Exception as e:
            print(f"[AUTH] ❌ Erro ao obter token: {e}")
            return False

    def get_token(self) -> Optional[str]:
        """Retorna token válido, renovando quando necessário."""
        if self._token is None or (self._expiry and time.time() > self._expiry):
            print("[AUTH] ⚠️ Token ausente ou expirado. Renovando...")
            ok = self.refresh_token()
            if not ok:
                return None
        return self._token

    def __str__(self):
        token = self.get_token()
        return token or ""