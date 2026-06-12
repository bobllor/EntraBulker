from tests.fixtures import graph, api, df
from backend.core.graph import Graph
from backend.core.parser import Parser
from backend.api.api import API
from backend.support.types import Response
from unittest.mock import patch
from requests import exceptions
from msal.oauth2cli.oauth2 import BrowserInteractionTimeoutError
from typing import Any
import pandas as pd

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

def test_authenticate_cache_graph(graph: Graph):
    graph._client_id = "12345" 
    graph._tenant_id = "12345"

    with patch("backend.core.graph.SerializableTokenCache.serialize") as serialmock:
        serialmock.return_value = "{'test': 'value'}"

        with patch("backend.core.graph.PublicClientApplication") as mock:
            mock.return_value.acquire_token_silent.return_value = {"access_token": "12345"}

            res: Response = graph.authenticate_with_cache()

            assert res["status"] == "success"

def test_authenticate_no_cache_graph(graph: Graph):
    graph._client_id = "12345" 
    graph._tenant_id = "12345"

    with patch("backend.core.graph.SerializableTokenCache.serialize") as serialmock:
        serialmock.return_value = "{'test': 'value'}"

        with patch("backend.core.graph.PublicClientApplication") as mock:
            mock.return_value.acquire_token_silent.return_value = None

            res: Response = graph.authenticate_with_cache()

            assert res["status"] == "error"

def test_graph_write_read_token_cache(graph: Graph):
    obj: dict[str, str] = {"test": "value", "another": "test"}
    graph.save_token_cache(obj)
    token_cache = graph.get_token_cache()

    assert token_cache._cache == obj

def test_graph_batch_under_twenty(graph: Graph, api: API, df:pd.DataFrame):
    res: Response = api._get_df(df)
    assert res["status"] and res["content"] is not None

    pres: Response = api._parse_df(res["content"])
    assert pres["status"] == "success" and pres["content"] is not None
    parser: Parser = pres["content"]

    user_data = api._extract_user_data(parser)
    user_json = api._create_json_users(user_data)
    headers = {"bearer": "12345", "content-type": "application/json"}
    batches = graph._create_batch(user_json, "POST", "/users", headers)

    assert len(batches[0]["requests"]) == len(user_json)

def test_graph_batch_over_twenty(graph: Graph, api: API, df: pd.DataFrame):
    res: Response = api._get_df(df)
    assert res["status"] and res["content"] is not None

    pres: Response = api._parse_df(res["content"])
    assert pres["status"] == "success" and pres["content"] is not None
    parser: Parser = pres["content"]

    user_data = api._extract_user_data(parser)
    user_json = api._create_json_users(user_data)
    
    # 17 each based on the fixed DF data
    new_data = user_json + user_json + user_json
    base_len = len(new_data)
    headers = {"bearer": "12345", "content-type": "application/json"}

    batches = graph._create_batch(new_data, "POST", "/user", headers)

    new_len: int = 0
    for b in batches:
        new_len += len(b["requests"])
    
    assert base_len == new_len and len(batches) == 3

def test_graph_retry_users(graph: Graph, api: API, df: pd.DataFrame):
    res: Response = api._get_df(df)
    assert res["status"] and res["content"] is not None

    pres: Response = api._parse_df(res["content"])
    assert pres["status"] == "success" and pres["content"] is not None
    parser: Parser = pres["content"]

    user_data = api._extract_user_data(parser)
    user_json = api._create_json_users(user_data)

    retry_time = 0
    with patch("backend.core.graph.Graph._post_batch") as mock: 
        mock.return_value = [
            {
                "responses": [
                    {
                    "id": "1",
                    "status": 429,
                    "headers": {
                        # not sure if this is how they structured it
                        "Retry-After": retry_time,
                        },
                    },
                    {
                        "id": "2",
                        "status": 429,
                        "headers": {
                            "Retry-After": retry_time,
                        },
                    }
                ],
            }
        ]

        # expects both to fail
        info = graph._create_users_retry(user_json, retry_time)
        assert len(info.failed_users) == 2 and len(info.retry_users) == 0

def test_graph_create_retry_users(graph: Graph, api: API, df: pd.DataFrame):
    res: Response = api._get_df(df)
    assert res["status"] and res["content"] is not None

    pres: Response = api._parse_df(res["content"])
    assert pres["status"] == "success" and pres["content"] is not None
    parser: Parser = pres["content"]

    user_data = api._extract_user_data(parser)
    user_json = api._create_json_users(user_data)

    graph._tenant_id = "12345"
    graph._client_id = "12345"
    
    with patch("backend.core.graph.PublicClientApplication") as mock1:
        mock1.return_value.acquire_token_silent.return_value = None
        mock1.return_value.acquire_token_interactive.return_value = {"access_token": "12345"}

        with patch("backend.core.graph.Graph._post_batch") as mock2: 
            # first one forces a retry
            # second one ensures the retry is successful
            mock2.side_effect = [
                [
                    {
                        "responses": [
                            {
                                "id": "1",
                                "status": 200,   
                            },
                            {
                                "id": "2",
                                "status": 429,
                                "headers": {
                                    "Retry-After": 0,
                                }
                            }
                        ]
                    }
                ],
                [
                    {
                        "responses": [
                            {
                                "id": "1",
                                "status": 200,
                            }
                        ]
                    }
                ]
            ]

            res = graph.create_users(user_json)
            assert res["status"] == "success"

            assert graph.create_batch_info is not None and len(graph.create_batch_info.created_users) == 2 \
                and len(graph.create_batch_info.failed_users) == 0
        
def test_graph_create_retry_fail_users(graph: Graph, api: API, df: pd.DataFrame):
    res: Response = api._get_df(df)
    assert res["status"] and res["content"] is not None

    pres: Response = api._parse_df(res["content"])
    assert pres["status"] == "success" and pres["content"] is not None
    parser: Parser = pres["content"]

    user_data = api._extract_user_data(parser)
    user_json = api._create_json_users(user_data)

    graph._tenant_id = "12345"
    graph._client_id = "12345"
    
    with patch("backend.core.graph.PublicClientApplication") as mock1:
        mock1.return_value.acquire_token_silent.return_value = None
        mock1.return_value.acquire_token_interactive.return_value = {"access_token": "12345"}

        with patch("backend.core.graph.Graph._post_batch") as mock2: 
            # ensures both mocks fail
            mock2.return_value = [
                {
                    "responses": [
                        {
                            "id": "1",
                            "status": 429,
                            "headers": {
                                "Retry-After": 0,
                            }  
                        },
                        {
                            "id": "2",
                            "status": 429,
                            "headers": {
                                "Retry-After": 0,
                            }
                        }
                    ]
                }
            ]

            res = graph.create_users(user_json)
            assert res["status"] != "success"

            assert graph.create_batch_info is not None and len(graph.create_batch_info.created_users) == 0 \
                and len(graph.create_batch_info.failed_users) == 2