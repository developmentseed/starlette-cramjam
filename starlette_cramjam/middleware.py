"""starlette_cramjam.middleware."""

import io
from typing import Any, Optional, Set

import cramjam

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class CompressionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 500,
        exclude_path: Optional[Set[str]] = None,
        exclude_mediatype: Optional[Set[str]] = None,
    ) -> None:
        self.app = app
        self.minimum_size = minimum_size
        self.exclude_path = exclude_path or set()
        self.exclude_mediatype = exclude_mediatype or set()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            accepted_encoding = headers.get("Accept-Encoding", "")

            if "br" in accepted_encoding:
                responder = CompressionResponder(
                    self.app, cramjam.brotli, "br", self.minimum_size,
                )
                await responder(scope, receive, send)
                return

            elif "gzip" in accepted_encoding:
                responder = CompressionResponder(
                    self.app, cramjam.gzip, "gzip", self.minimum_size,
                )
                await responder(scope, receive, send)
                return

            elif "deflate" in accepted_encoding:
                responder = CompressionResponder(
                    self.app, cramjam.deflate, "deflate", self.minimum_size,
                )
                await responder(scope, receive, send)
                return

        await self.app(scope, receive, send)


class CompressionResponder:
    def __init__(
        self, app: ASGIApp, compressor: Any, encoding_name: str, minimum_size: int
    ) -> None:

        self.app = app
        self.compressor = compressor
        self.encoding_name = encoding_name
        self.minimum_size = minimum_size

        self.send = unattached_send  # type: Send
        self.initial_message = {}  # type: Message
        self.started = False
        self.buffer = io.BytesIO()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.send = send
        await self.app(scope, receive, self.send_with_compression)

    async def send_with_compression(self, message: Message) -> None:

        message_type = message["type"]

        if message_type == "http.response.start":
            # Don't send the initial message until we've determined how to
            # modify the outgoing headers correctly.
            self.initial_message = message

        elif message_type == "http.response.body" and not self.started:
            self.started = True
            body = message.get("body", b"")
            more_body = message.get("more_body", False)

            if len(body) < self.minimum_size and not more_body:
                # Don't apply compression to small outgoing responses.
                await self.send(self.initial_message)
                await self.send(message)

            elif not more_body:
                # Standard compressed response.
                self.buffer.write(self.compressor.compress(body))
                body = self.buffer.getvalue()

                headers = MutableHeaders(raw=self.initial_message["headers"])
                headers["Content-Encoding"] = self.encoding_name
                headers["Content-Length"] = str(len(body))
                headers.add_vary_header("Accept-Encoding")
                message["body"] = body

                await self.send(self.initial_message)
                await self.send(message)

            else:
                # Initial body in streaming compressed response.
                headers = MutableHeaders(raw=self.initial_message["headers"])
                headers["Content-Encoding"] = self.encoding_name
                headers.add_vary_header("Accept-Encoding")
                del headers["Content-Length"]

                self.buffer.write(self.compressor.compress(body))
                message["body"] = self.compressor.compress(body)
                self.buffer.seek(0)
                self.buffer.truncate()

                await self.send(self.initial_message)
                await self.send(message)

        elif message_type == "http.response.body":
            # Remaining body in streaming compressed response.
            body = message.get("body", b"")
            more_body = message.get("more_body", False)

            if not body:
                await self.send(message)
                return

            self.buffer.write(self.compressor.compress(body))

            if not more_body:
                message["body"] = self.buffer.getvalue()
                self.buffer.close()
                await self.send(message)
                return

            message["body"] = self.buffer.getvalue()
            self.buffer.seek(0)
            self.buffer.truncate()
            await self.send(message)

            # self.buffer.write(self.compressor.compress(body))
            # if not more_body:
            #     self.gzip_file.close()

            # message["body"] = self.gzip_buffer.getvalue()
            # self.gzip_buffer.seek(0)
            # self.gzip_buffer.truncate()

            # await self.send(message)


async def unattached_send(message: Message) -> None:
    raise RuntimeError("send awaitable not set")  # pragma: no cover
