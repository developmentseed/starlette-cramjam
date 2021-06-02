"""Main test for cramjam middleware.

This tests are the same as the ones from starlette.tests.middleware.test_gzip but using multiple encoding.

"""
import pytest

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, StreamingResponse
from starlette.testclient import TestClient
from starlette_cramjam import CompressionMiddleware


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_compressed_responses(method):
    app = Starlette()

    app.add_middleware(CompressionMiddleware)

    @app.route("/")
    def homepage(request):
        return PlainTextResponse("x" * 4000, status_code=200)

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.text == "x" * 4000
    assert response.headers["Content-Encoding"] == method
    assert int(response.headers["Content-Length"]) < 4000


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_streaming_response(method):
    app = Starlette()
    app.add_middleware(CompressionMiddleware, minimum_size=1)

    @app.route("/")
    def homepage(request):
        async def generator(bytes, count):
            for _ in range(count):
                yield bytes

        streaming = generator(bytes=b"x" * 400, count=10)
        return StreamingResponse(streaming, status_code=200)

    client = TestClient(app)

    response = client.get("/", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.headers["Content-Encoding"] == method
    assert "Content-Length" not in response.headers
    assert response.text == "x" * 4000


def test_not_in_accept_encoding():
    app = Starlette()

    app.add_middleware(CompressionMiddleware)

    @app.route("/")
    def homepage(request):
        return PlainTextResponse("x" * 4000, status_code=200)

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": "identity"})
    assert response.status_code == 200
    assert response.text == "x" * 4000
    assert "Content-Encoding" not in response.headers
    assert int(response.headers["Content-Length"]) == 4000


def test_ignored_for_small_responses():
    app = Starlette()

    app.add_middleware(CompressionMiddleware)

    @app.route("/")
    def homepage(request):
        return PlainTextResponse("OK", status_code=200)

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": "gzip"})
    assert response.status_code == 200
    assert response.text == "OK"
    assert "Content-Encoding" not in response.headers
    assert int(response.headers["Content-Length"]) == 2
