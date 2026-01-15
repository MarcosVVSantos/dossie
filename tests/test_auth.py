from src.settings.auth import Auth
from src.settings.config import config


def test_auth_missing_credentials(monkeypatch):
    # Backup
    old_email = config.email
    old_password = config.password
    try:
        config.email = ''
        config.password = ''
        auth = Auth()
        token = auth.get_token()
        assert token is None
    finally:
        config.email = old_email
        config.password = old_password