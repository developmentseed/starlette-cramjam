"""Main test for cramjam middleware.

This tests are the same as the ones from starlette.tests.middleware.test_gzip but using multiple encoding.

"""

import sys

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse, Response, StreamingResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from starlette_cramjam.compression import Compression
from starlette_cramjam.middleware import CompressionMiddleware, get_compression_backend


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_compressed_responses(method):
    def homepage(request):
        return PlainTextResponse("x" * 4000, status_code=200)

    app = Starlette(
        routes=[Route("/", endpoint=homepage)],
        middleware=[
            Middleware(CompressionMiddleware),
        ],
    )

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.text == "x" * 4000
    assert response.headers["Content-Encoding"] == method
    assert sys.getsizeof(response.content) > int(response.headers["Content-Length"])


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_compression_level(method):
    def homepage(request):
        return PlainTextResponse("x" * 4000, status_code=200)

    app = Starlette(
        routes=[Route("/", endpoint=homepage)],
        middleware=[
            Middleware(CompressionMiddleware, compression_level=3),
        ],
    )

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.text == "x" * 4000
    assert response.headers["Content-Encoding"] == method
    assert sys.getsizeof(response.content) > int(response.headers["Content-Length"])


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_streaming_response(method):
    def homepage(request):
        async def generator(bytes, count):
            for _ in range(count):
                yield bytes

        streaming = generator(bytes=b"x" * 400, count=10)
        return StreamingResponse(streaming, status_code=200)

    app = Starlette(
        routes=[Route("/", endpoint=homepage)],
        middleware=[
            Middleware(CompressionMiddleware, minimum_size=1),
        ],
    )

    client = TestClient(app)

    response = client.get("/", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.headers["Content-Encoding"] == method
    assert "Content-Length" not in response.headers
    assert response.text == "x" * 4000


def test_not_in_accept_encoding():
    def homepage(request):
        return PlainTextResponse("x" * 4000, status_code=200)

    app = Starlette(
        routes=[Route("/", endpoint=homepage)],
        middleware=[
            Middleware(CompressionMiddleware),
        ],
    )

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": "identity"})
    assert response.status_code == 200
    assert response.text == "x" * 4000
    assert "Content-Encoding" not in response.headers
    assert int(response.headers["Content-Length"]) == 4000


def test_ignored_for_small_responses():
    def homepage(request):
        return PlainTextResponse("OK", status_code=200)

    app = Starlette(
        routes=[Route("/", endpoint=homepage)],
        middleware=[
            Middleware(CompressionMiddleware),
        ],
    )

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": "gzip"})
    assert response.status_code == 200
    assert response.text == "OK"
    assert "Content-Encoding" not in response.headers
    assert int(response.headers["Content-Length"]) == 2


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_compressed_skip_on_content_type(method):
    def homepage(request):
        return Response(b"foo" * 1000, status_code=200, media_type="image/png")

    def foo(request):
        return Response(b"foo" * 1000, status_code=200, media_type="image/jpeg")

    app = Starlette(
        routes=[
            Route("/", endpoint=homepage),
            Route("/foo", endpoint=foo),
        ],
        middleware=[
            Middleware(CompressionMiddleware, exclude_mediatype={"image/png"}),
        ],
    )

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert "Content-Encoding" not in response.headers

    response = client.get("/foo", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.headers["Content-Encoding"] == method


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_compressed_skip_on_path(method):
    def homepage(request):
        return PlainTextResponse("yep", status_code=200)

    def foo(request):
        return Response("also yep but with /foo", status_code=200)

    def foo2(request):
        return Response("also yep but with /dontskip/foo", status_code=200)

    app = Starlette(
        routes=[
            Route("/", endpoint=homepage),
            Route("/foo", endpoint=foo),
            Route("/dontskip/foo", endpoint=foo2),
        ],
        middleware=[
            Middleware(CompressionMiddleware, exclude_path={"^/f.+"}, minimum_size=0),
        ],
    )

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.headers["Content-Encoding"] == method

    response = client.get("/dontskip/foo", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.headers["Content-Encoding"] == method

    response = client.get("/foo", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert "Content-Encoding" not in response.headers


@pytest.mark.parametrize(
    "compression,expected",
    [
        ([], "gzip"),
        ([Compression.gzip], "gzip"),
        ([Compression.br, Compression.gzip], "br"),
        ([Compression.gzip, Compression.br], "gzip"),
    ],
)
def test_compressed_skip_on_encoder(compression, expected):
    def homepage(request):
        return PlainTextResponse("x" * 4000, status_code=200)

    app = Starlette(
        routes=[
            Route("/", endpoint=homepage),
        ],
        middleware=[
            Middleware(CompressionMiddleware, compression=compression),
        ],
    )

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": "br,gzip,deflate"})
    assert response.headers["Content-Encoding"] == expected


@pytest.mark.parametrize(
    "compression,header,expected",
    [
        # deflate preferred but only gzip available
        ([Compression.gzip], "deflate, gzip;q=0.8", Compression.gzip),
        # deflate preferred and available
        (
            [Compression.gzip, Compression.deflate],
            "deflate, gzip;q=0.8",
            Compression.deflate,
        ),
        # asking for deflate or gzip but only br is available
        ([Compression.br], "deflate, gzip;q=0.8", None),
        # no accepted-encoding
        ([Compression.br], "", None),
        # br is prefered and available
        (
            [Compression.gzip, Compression.br, Compression.deflate],
            "br;q=1.0, gzip;q=0.8",
            Compression.br,
        ),
        # br and gzip are equally preferred but gzip is the first available
        ([Compression.gzip, Compression.br], "br;q=1.0, gzip;q=1.0", Compression.gzip),
        # br and gzip are equally preferred but br is the first available
        ([Compression.br, Compression.gzip], "br;q=1.0, gzip;q=1.0", Compression.br),
        # br and gzip are available and client has no preference
        ([Compression.br, Compression.gzip], "*;q=1.0", Compression.br),
        # invalid br quality so ignored
        ([Compression.br, Compression.gzip], "br;q=aaa, gzip", Compression.gzip),
        # br quality is set to 0
        ([Compression.br, Compression.gzip], "br;q=0.0, gzip", Compression.gzip),
    ],
)
def test_get_compression_backend(compression, header, expected):
    """Make sure we use the right compression."""
    assert get_compression_backend(header, compression) == expected
