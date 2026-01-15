import os
from pathlib import Path
import tempfile

from src.settings.env_loader import load_env


def test_load_env_missing_required(tmp_path):
    # Cria um .env vazio
    p = tmp_path / ".env"
    p.write_text("")
    try:
        load_env(path=str(p), required_vars=["SOME_VAR"], verbose=False)
        assert False, "Expected RuntimeError due to missing variable"
    except RuntimeError as e:
        assert "SOME_VAR" in str(e)


def test_load_env_with_vars(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("SOME_VAR=ok\nANOTHER=1")
    out = load_env(path=str(p), required_vars=["SOME_VAR"], verbose=False)
    assert out["SOME_VAR"] == "ok"