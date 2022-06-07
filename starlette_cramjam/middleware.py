"""starlette_cramjam.middleware."""

import re
from typing import Any, List, Optional, Set

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from starlette_cramjam.compression import Compression

ACCEPT_ENCODING_PATTERN = r"^(?P<compression>[a-z]+|\*)(;q=(?P<qvalue>[\w,.]+))?"

DEFAULT_BACKENDS = [
    Compression.gzip,
    Compression.deflate,
    Compression.br,
]


def get_compression_backend(
    accepted_encoding: str, compressions: List[Compression]
) -> Optional[Compression]:
    """Return Compression backend based on default compression and accepted preference.

    Links:
    - https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
    - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Encoding

    """
    # Parse Accepted-Encoding value `gzip, deflate;q=0.1`
    encoding_values = {}
    for encoding in accepted_encoding.replace(" ", "").split(","):
        matched = re.match(ACCEPT_ENCODING_PATTERN, encoding)
        if matched:
            name, q = matched.groupdict().values()
            try:
                quality = float(q) if q else 1.0
            except ValueError:
                quality = 0

            # if quality is 0 we ignore encoding
            if quality:
                encoding_values[name] = quality

    # Create Preference matrix
    encoding_preference = {
        v: [n for (n, q) in encoding_values.items() if q == v]
        for v in sorted({q for q in encoding_values.values()}, reverse=True)
    }

    # Loop through available compression and encoding preference
    for _, pref in encoding_preference.items():
        for backend in compressions:
            if backend.name in pref:
                return backend

    # If no specified encoding is supported but "*" is accepted,
    # take one of the available compressions.
    if "*" in encoding_values and compressions:
        return compressions[0]

    return None


class CompressionMiddleware:
    """Starlette Cramjam MiddleWare."""

    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 500,
        compression: Optional[List[Compression]] = None,
        exclude_path: Optional[Set[str]] = None,
        exclude_mediatype: Optional[Set[str]] = None,
    ) -> None:
        """Init CompressionMiddleware.

        Args:
            app (ASGIApp): starlette/FastAPI application.
            minimum_size: Minimal size, in bytes, for appliying compression. Defaults to 500.
            compression (list): List of available compression backend. Order will define the backend preference.
            exclude_path (set): Set of regex expression to use to exclude compression for request path. Defaults to {}.
            exclude_mediatype (set): Set of media-type for which to exclude compression. Defaults to {}.

        """
        self.app = app
        self.minimum_size = minimum_size
        self.exclude_path = {re.compile(p) for p in exclude_path or set()}
        self.exclude_mediatype = exclude_mediatype or set()
        self.compression = compression or DEFAULT_BACKENDS

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle call."""
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            accepted_encoding = headers.get("Accept-Encoding", "")

            if self.exclude_path:
                skip = any([x.fullmatch(scope["path"]) for x in self.exclude_path])
            else:
                skip = False

            backend = get_compression_backend(accepted_encoding, self.compression)
            if not skip and backend:
                responder = CompressionResponder(
                    self.app,
                    backend.compress.Compressor(),
                    backend.name,
                    self.minimum_size,
                    self.exclude_mediatype,
                )
                await responder(scope, receive, send)
                return

        await self.app(scope, receive, send)


class CompressionResponder:
    """Responder class."""

    def __init__(
        self,
        app: ASGIApp,
        compressor: Any,
        encoding_name: str,
        minimum_size: int,
        exclude_mediatype: Set[str],
    ) -> None:
        """Init."""
        self.app = app
        self.compressor = compressor
        self.encoding_name = encoding_name
        self.minimum_size = minimum_size
        self.exclude_mediatype = exclude_mediatype
        self.send = unattached_send  # type: Send
        self.initial_message = {}  # type: Message
        self.started = False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle call."""
        self.send = send
        await self.app(scope, receive, self.send_with_compression)

    async def send_with_compression(self, message: Message) -> None:
        """Compress response."""
        message_type = message["type"]

        if message_type == "http.response.start":
            # Don't send the initial message until we've determined how to
            # modify the outgoing headers correctly.
            self.initial_message = message

        elif message_type == "http.response.body" and not self.started:
            self.started = True
            body = message.get("body", b"")
            more_body = message.get("more_body", False)

            headers = MutableHeaders(raw=self.initial_message["headers"])

            if headers.get("Content-Type") in self.exclude_mediatype:
                # Don't apply compression if mediatype should be excluded
                await self.send(self.initial_message)
                await self.send(message)

            elif len(body) < self.minimum_size and not more_body:
                # Don't apply compression to small outgoing responses.
                await self.send(self.initial_message)
                await self.send(message)

            elif not more_body:
                # Standard compressed response.
                self.compressor.compress(body)
                body = bytes(self.compressor.finish())

                headers["Content-Encoding"] = self.encoding_name
                headers["Content-Length"] = str(len(body))
                headers.add_vary_header("Accept-Encoding")
                message["body"] = body

                await self.send(self.initial_message)
                await self.send(message)

            else:
                # Initial body in streaming compressed response.
                headers["Content-Encoding"] = self.encoding_name
                headers.add_vary_header("Accept-Encoding")

                # https://gist.github.com/CMCDragonkai/6bfade6431e9ffb7fe88#content-length
                # Content-Length header will not allow streaming
                del headers["Content-Length"]
                self.compressor.compress(body)
                message["body"] = bytes(self.compressor.flush())

                await self.send(self.initial_message)
                await self.send(message)

        elif message_type == "http.response.body":
            # Remaining body in streaming compressed response.
            body = message.get("body", b"")
            more_body = message.get("more_body", False)

            self.compressor.compress(body)
            if not more_body:
                message["body"] = bytes(self.compressor.finish())
                await self.send(message)
                return
            message["body"] = bytes(self.compressor.flush())

            await self.send(message)


async def unattached_send(message: Message) -> None:
    """Unable to send."""
    raise RuntimeError("send awaitable not set")  # pragma: no cover
