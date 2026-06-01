from tests.fixtures import graph
from backend.core.graph import Graph
from backend.support.types import Response
from unittest.mock import patch
from requests import exceptions
import tests.utils as ttils

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