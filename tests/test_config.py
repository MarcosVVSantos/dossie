import os
from src.settings.config import Config


def test_config_from_env_missing(monkeypatch, tmp_path):
    # Ensure missing required vars raises
    monkeypatch.delenv('email', raising=False)
    monkeypatch.delenv('password', raising=False)
    try:
        Config.from_env()
        assert False, 'Expected RuntimeError when required vars missing'
    except RuntimeError:
        pass


def test_config_from_env_ok(monkeypatch):
    monkeypatch.setenv('email', 'a@b.com')
    monkeypatch.setenv('password', 'secret')
    monkeypatch.setenv('paymentsUrl', 'https://example')
    cfg = Config.from_env()
    assert cfg.email == 'a@b.com'
    assert cfg.paymentsUrl == 'https://example'