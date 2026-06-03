from tests.fixtures import graph
from backend.core.graph import Graph
from backend.support.types import Response
from unittest.mock import patch
from requests import exceptions
from msal.oauth2cli.oauth2 import BrowserInteractionTimeoutError
from typing import Any

def test_authenticate_normal(graph: Graph):
    graph._tenant_id = "12345"
    graph._client_id = "12345"
    token: str = "123457890"

    with patch("backend.core.graph.PublicClientApplication") as mock:
        mock.return_value.acquire_token_silent.return_value = None
        mock.return_value.acquire_token_interactive.return_value = {"access_token": token}
        res: Response = graph.authenticate()

        assert res["status"] == "success" and graph.access_token == token

def test_authenticate_app_creation_fail(graph: Graph):
    res: Response = graph.authenticate()

    assert res["status"] == "error"

def test_fail_authenticate(graph: Graph):
    graph._tenant_id = "12345"
    graph._client_id = "12345"

    with patch("backend.core.graph.PublicClientApplication") as mock:
        mock.return_value.acquire_token_silent.return_value = None
        mock.return_value.acquire_token_interactive.return_value = {
            "error": "ERR_TOKEN_RETRIEVAL",
            "error_description": "An error occurred while retrieving token",
            "correlation_id": "abcd-12345"
        }
        res: Response = graph.authenticate()

        assert res["status"] == "error"

def test_exception_authenticate(graph: Graph):
    graph._tenant_id = "12345"
    graph._client_id = "12345"

    with patch("backend.core.graph.PublicClientApplication") as mock:
        mock.return_value.acquire_token_silent.return_value = None
        mock.return_value.acquire_token_interactive.side_effect = BrowserInteractionTimeoutError("Authentication timed out")
        res: Response = graph.authenticate()

        assert res["status"] == "error"

def test_graph_exceptions(graph: Graph):
    graph._client_id = "12345" 
    graph._tenant_id = "12345" 

    with patch("backend.core.graph.PublicClientApplication") as mock:
        mock.return_value.acquire_token_silent.return_value = None
        mock.return_value.acquire_token_interactive.return_value = {"access_token": "12345"}

        with patch("backend.core.graph.requests.post") as mock2:
            exception_values: list[exceptions.RequestException] = [
                exceptions.Timeout("Request timed out"),
                exceptions.ConnectionError("Request failed to connect"),
                exceptions.HTTPError("HTTP error"),
                ValueError("Value error")
            ]

            for exc in exception_values:
                mock2.side_effect = exc
                res: Response = graph.create_users([
                    {
                        "accountEnabled": True,
                        "displayName": "John Doe",
                        "givenName": "John",
                        "surname": "Doe",
                        "mailNickname": "John.Doe",
                        "userPrincipalName": "John.Doe@domain.com",
                        "passwordProfile": {
                            "forceChangePasswordNextSignIn": True,
                            "password": "12345",
                        },
                        "userType": "member",
                    }
                ])

                assert res["status"] == "error"

def test_graph_clear_cache(graph: Graph):
    recent_user: str = "test@domain.com"
    accounts: list[dict[str, Any]] = [{"username": recent_user}]

    graph.cache_reader.update("account_cache", accounts)
    graph.cache_reader.update("recent_username", recent_user)

    graph._client_id = "12345" 
    graph._tenant_id = "12345"

    with patch("backend.core.graph.SerializableTokenCache.serialize") as serialmock:
        serialmock.return_value = "{'test': 'value'}"

        with patch("backend.core.graph.PublicClientApplication") as mock:
            graph.authenticate()

            base_token_cache: str = graph.token_cache_writer.load()
            base_cache_reader: dict[str, Any] = graph.cache_reader.get_content().copy()
            
            mock.return_value.acquire_token_silent.return_value = None
            mock.return_value.acquire_token_interactive.return_value = {"access_token": "12345"}

            res: Response = graph.clear_cache()

            new_token_cache: str = graph.token_cache_writer.load()
            new_cache_reader: dict[str, Any] = graph.cache_reader.get_content()

            assert res["status"] == "success"
            assert [not v for v in new_cache_reader.values()]
            
            assert base_token_cache != new_token_cache and new_cache_reader != base_cache_reader

def test_graph_write_read_token_cache(graph: Graph):
    obj: dict[str, str] = {"test": "value", "another": "test"}
    graph.save_token_cache(obj)
    token_cache = graph.get_token_cache()

    assert token_cache._cache == obj