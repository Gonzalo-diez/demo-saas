"""IP con la que se cuenta el rate limit cuando el backend está detrás de un proxy."""
import pytest
from starlette.requests import Request

from app.core.config import settings
from app.core.rate_limit import client_ip


def _request(forwarded: str | None = None, peer: str = "10.0.0.5") -> Request:
    headers = []
    if forwarded is not None:
        headers.append((b"x-forwarded-for", forwarded.encode()))
    return Request({"type": "http", "headers": headers, "client": (peer, 1234), "method": "GET", "path": "/"})


@pytest.fixture()
def hops(monkeypatch):
    def set_hops(value: int):
        monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", value)
    return set_hops


class TestClientIp:
    def test_default_uses_connection_ip_and_ignores_forwarded_header(self, hops):
        hops(0)
        # Un cliente cualquiera no puede cambiar su cupo mandando X-Forwarded-For.
        assert client_ip(_request("1.2.3.4")) == "10.0.0.5"

    def test_one_trusted_proxy_uses_the_ip_it_appended(self, hops):
        hops(1)
        assert client_ip(_request("203.0.113.7")) == "203.0.113.7"

    def test_spoofed_left_values_are_ignored(self, hops):
        hops(1)
        # El cliente mandó "9.9.9.9"; nuestro proxy agregó la IP real al final.
        assert client_ip(_request("9.9.9.9, 203.0.113.7")) == "203.0.113.7"

    def test_two_proxies(self, hops):
        hops(2)
        assert client_ip(_request("9.9.9.9, 203.0.113.7, 10.1.1.1")) == "203.0.113.7"

    def test_falls_back_to_connection_ip_when_header_is_missing_or_short(self, hops):
        hops(1)
        assert client_ip(_request(None)) == "10.0.0.5"
        hops(2)
        assert client_ip(_request("203.0.113.7")) == "10.0.0.5"

    def test_different_users_get_different_buckets_behind_the_proxy(self, hops):
        hops(1)
        assert client_ip(_request("198.51.100.1")) != client_ip(_request("198.51.100.2"))
