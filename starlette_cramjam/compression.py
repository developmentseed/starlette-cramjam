"""starlette_cramjam.compression."""

from enum import Enum
from types import DynamicClassAttribute

import cramjam

compression_backends = {
    "br": cramjam.brotli,
    "deflate": cramjam.deflate,
    "gzip": cramjam.gzip,
}


class Compression(str, Enum):
    """Responses Media types formerly known as MIME types."""

    gzip = "gzip"
    br = "br"
    deflate = "deflate"

    @DynamicClassAttribute
    def compress(self):
        """Return cramjam backend."""
        return compression_backends[self._name_]
