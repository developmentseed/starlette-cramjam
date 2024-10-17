"""starlette_cramjam.compression."""

from enum import Enum
from types import DynamicClassAttribute

import cramjam

compression_backends = {
    "br": cramjam.brotli,  # min: 0, max: 11, default: 11
    "deflate": cramjam.deflate,  # min: 0, max: 9, default: 6
    "gzip": cramjam.gzip,  # min: 0, max: 9, default: 6
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
