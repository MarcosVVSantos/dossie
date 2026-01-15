from src.settings.http import create_session, request_with_timeout
import requests


def test_create_session_has_timeout_attr():
    s = create_session(retries=1, backoff_factor=0.1)
    assert hasattr(s, 'request_timeout')


def test_request_with_timeout_invalid_url():
    s = create_session(retries=1)
    try:
        # This should raise a requests exception but should not hang
        request_with_timeout(s, 'GET', 'http://127.0.0.1:9', timeout=1)
    except requests.exceptions.RequestException:
        assert True
    except Exception:
        assert False, 'Unexpected exception type'