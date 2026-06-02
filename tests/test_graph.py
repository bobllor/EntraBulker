from tests.fixtures import graph
from backend.core.graph import Graph
from backend.support.types import Response
from unittest.mock import patch
from requests import exceptions
from msal.oauth2cli.oauth2 import BrowserInteractionTimeoutError

def test_graph_is_authenticated(graph: Graph):
    graph.token = "fdsa"

    with patch("backend.core.graph.requests.get") as mock:
        mock.return_value.json.return_value = {}
        res: Response = graph.is_authenticated()

        assert res["status"] == "success" and res["content"]

def test_graph_is_not_authenticated(graph: Graph):
    graph.token = "fdsa"

    with patch("backend.core.graph.requests.get") as mock:
        mock.return_value.ok = False
        res: Response = graph.is_authenticated()

        assert res["status"] == "success" and not res["content"]

def test_graph_is_not_authenticated_no_token(graph: Graph):
    res: Response = graph.is_authenticated()

    assert res["status"] == "success" and not res["content"]

def test_authenticate(graph: Graph):
    graph._tenant_id = "12345"
    graph._client_id = "12345"
    token: str = "123457890"

    with patch("backend.core.graph.PublicClientApplication") as mock:
        mock.return_value.acquire_token_interactive.return_value = {"access_token": token}
        res: Response = graph.authenticate()

        assert res["status"] == "success" and token in graph.bearer

def test_authenticate_app_creation_fail(graph: Graph):
    res: Response = graph.authenticate()

    assert res["status"] == "error"

def test_authenticate_fail(graph: Graph):
    graph._tenant_id = "12345"
    graph._client_id = "12345"

    with patch("backend.core.graph.PublicClientApplication") as mock:
        mock.return_value.acquire_token_interactive.return_value = {
            "error": "ERR_TOKEN_RETRIEVAL",
            "error_description": "An error occurred while retrieving token",
            "id": "abcd-12345"
        }
        res: Response = graph.authenticate()

        assert res["status"] == "error"

def test_authenticate_exception_fail(graph: Graph):
    graph._tenant_id = "12345"
    graph._client_id = "12345"

    with patch("backend.core.graph.PublicClientApplication") as mock:
        mock.return_value.acquire_token_interactive.side_effect = BrowserInteractionTimeoutError("Authentication timed out")
        res: Response = graph.authenticate()

        assert res["status"] == "error"

def test_graph_exception(graph: Graph):
    with patch("backend.core.graph.requests.get") as mock:
        exception_values: list[exceptions.RequestException] = [
            exceptions.Timeout("Request timed out"),
            exceptions.ConnectionError("Request failed to connect"),
            exceptions.HTTPError("HTTP error"),
            ValueError("Value error")
        ]

        graph.token = "fdsaf"

        for exc in exception_values:
            mock.side_effect = exc
            res: Response = graph.is_authenticated()

            assert res["status"] == "error"