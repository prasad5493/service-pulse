"""Unit tests for the check logic. No network calls — requests is mocked."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from checks import CheckResult, check_endpoint, load_endpoints  # noqa: E402

ENDPOINT = {"name": "test", "url": "https://example.com", "timeout_seconds": 5}


def _response(status_code: int) -> Mock:
    response = Mock()
    response.status_code = status_code
    return response


def test_healthy_endpoint_passes():
    with patch("checks.requests.get", return_value=_response(200)):
        result = check_endpoint(ENDPOINT)
    assert result.ok is True
    assert result.status_code == 200
    assert result.latency_ms is not None


def test_redirect_still_counts_as_healthy():
    with patch("checks.requests.get", return_value=_response(301)):
        assert check_endpoint(ENDPOINT).ok is True


def test_server_error_fails():
    with patch("checks.requests.get", return_value=_response(503)):
        result = check_endpoint(ENDPOINT)
    assert result.ok is False
    assert result.status_code == 503


def test_timeout_fails_with_error_name():
    with patch("checks.requests.get", side_effect=requests.Timeout()):
        result = check_endpoint(ENDPOINT)
    assert result.ok is False
    assert result.status_code is None
    assert result.error == "Timeout"


def test_config_file_is_valid():
    endpoints = load_endpoints()
    assert len(endpoints) > 0
    for endpoint in endpoints:
        assert endpoint["url"].startswith("https://")
        assert endpoint["name"]


def test_result_is_a_simple_dataclass():
    result = CheckResult(
        name="x", url="https://x", ok=True, status_code=200, latency_ms=12.3
    )
    assert result.error is None
