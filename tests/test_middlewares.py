"""Main test for cramjam middleware.

This tests are the same as the ones from starlette.tests.middleware.test_gzip but using multiple encoding.

"""
import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response, StreamingResponse
from starlette.testclient import TestClient

from starlette_cramjam.compression import Compression
from starlette_cramjam.middleware import CompressionMiddleware, get_compression_backend


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


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_compressed_skip_on_content_type(method):
    app = Starlette()

    app.add_middleware(CompressionMiddleware, exclude_mediatype={"image/png"})

    @app.route("/")
    def homepage(request):
        return Response(b"foo" * 1000, status_code=200, media_type="image/png")

    @app.route("/foo")
    def foo(request):
        return Response(b"foo" * 1000, status_code=200, media_type="image/jpeg")

    client = TestClient(app)
    response = client.get("/", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert "Content-Encoding" not in response.headers

    response = client.get("/foo", headers={"accept-encoding": method})
    assert response.status_code == 200
    assert response.headers["Content-Encoding"] == method


@pytest.mark.parametrize("method", ["br", "gzip", "deflate"])
def test_compressed_skip_on_path(method):
    app = Starlette()

    app.add_middleware(CompressionMiddleware, exclude_path={"^/f.+"}, minimum_size=0)

    @app.route("/")
    def homepage(request):
        return PlainTextResponse("yep", status_code=200)

    @app.route("/foo")
    def foo(request):
        return Response("also yep but with /foo", status_code=200)

    @app.route("/dontskip/foo")
    def foo2(request):
        return Response("also yep but with /dontskip/foo", status_code=200)

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
    app = Starlette()

    app.add_middleware(CompressionMiddleware, compression=compression)

    @app.route("/")
    def homepage(request):
        return PlainTextResponse("x" * 4000, status_code=200)

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
