# starlette-cramjam

<p align="center">
  <em>Cramjam integration for Starlette ASGI framework.</em>
</p>
<p align="center">
  <a href="https://github.com/developmentseed/starlette-cramjam/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/starlette-cramjam/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://codecov.io/gh/developmentseed/starlette-cramjam" target="_blank">
      <img src="https://codecov.io/gh/developmentseed/starlette-cramjam/branch/master/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/starlette-cramjam" target="_blank">
      <img src="https://img.shields.io/pypi/v/starlette-cramjam?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://pypistats.org/packages/starlette-cramjam" target="_blank">
      <img src="https://img.shields.io/pypi/dm/starlette-cramjam.svg" alt="Downloads">
  </a>
  <a href="https://github.com/developmentseed/starlette-cramjam/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/starlette-cramjam.svg" alt="Downloads">
  </a>
</p>

---

**Source Code**: <a href="https://github.com/developmentseed/starlette-cramjam" target="_blank">https://github.com/developmentseed/starlette-cramjam</a>

---

The `starlette-cramjam` middleware aims to provide a unique Compression middleware to support **Brotli**, **GZip**, **Deflate** and **ZSTD** compression algorithms with a minimal requirement.

The middleware will compress responses for any request that includes "br", "gzip", "deflate" or "zstd" in the Accept-Encoding header.

As for the official `Starlette` middleware, the one provided by `starlette-cramjam` will handle both standard and streaming responses.

`stralette-cramjam` is built on top of [pyrus-cramjam](https://github.com/milesgranger/pyrus-cramjam) an *Extremely thin Python bindings to de/compression algorithms in Rust*.

## Installation

You can install `starlette-cramjam` from pypi

```python
$ pip install -U pip
$ pip install starlette-cramjam
```

or install from source:

```bash
$ pip install -U pip
$ pip install https://github.com/developmentseed/starlette-cramjam.git
```

## Usage

The following arguments are supported:

- **compression** (List of Compression) - List of available compression algorithm. **This list also defines the order of preference**. Defaults to `[Compression.gzip, Compression.deflate, Compression.br, Compression.zstd]`,
- **compression_level** (Integer) - Compression level to use, form `0` (None) to `11` (High). Defaults to cramjam internal defaults for each compression backend.
- **minimum_size** (Integer) - Do not compress responses that are smaller than this minimum size in bytes. Defaults to `500`.
- **exclude_path** (Set of string) - Do not compress responses in response to specific `path` requests. Entries have to be valid regex expressions. Defaults to `{}`.
- **exclude_mediatype** (Set of string) - Do not compress responses of specific media type (e.g `image/png`). Defaults to `{}`.

#### Minimal (defaults) example

```python
import uvicorn

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from starlette_cramjam.middleware import CompressionMiddleware

def index(request):
    return PlainTextResponse("Hello World")


app = Starlette(
    routes=[Route("/", endpoint=index)],
    middleware=[
        Middleware(CompressionMiddleware),
    ],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Using options

```python
import uvicorn

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from starlette_cramjam.compression import Compression
from starlette_cramjam.middleware import CompressionMiddleware

def index(request):
    return PlainTextResponse("Hello World")

def img(request):
    return Response(b"This is a fake body", status_code=200, media_type="image/jpeg")

def foo(request):
    return PlainTextResponse("Do not compress me.")


app = Starlette(
    routes=[
        Route("/", endpoint=index),
        Route("/image", endpoint=img),
        Route("/foo", endpoint=foo),
    ],
    middleware=[
        Middleware(
            CompressionMiddleware,
            compression=[Compression.gzip],  # Only support `gzip`
            compression_level=6,  # Compression level to use
            minimum_size=0,  # should compress everything
            exclude_path={"^/foo$"},  # do not compress response for the `/foo` request
            exclude_mediatype={"image/jpeg"},  # do not compress jpeg
        ),
    ],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Performance

```python
import gzip
import sys

import brotli
import cramjam
import httpx

page = httpx.get("https://github.com/developmentseed/starlette-cramjam").content

len(page)
# 347686

%timeit brotli.compress(page, quality=4)
# 1.77 ms ± 19.7 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)

sys.getsizeof(brotli.compress(page, quality=4))
# 48766

%timeit gzip.compress(page, compresslevel=6)
# 4.62 ms ± 28 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

sys.getsizeof(gzip.compress(page, compresslevel=6))
# 54888

# ------------
# With Cramjam
# ------------
%timeit cramjam.gzip.compress(page, level=6)
# 4.12 ms ± 57.3 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

cramjam.gzip.compress(page, level=6).len()
# 55221

%timeit cramjam.brotli.compress(page, level=4)
# 2.3 ms ± 48.5 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

cramjam.brotli.compress(page, level=4).len()
# 48742
```

Ref: https://github.com/fullonic/brotli-asgi?tab=readme-ov-file#performance

## Changes

See [CHANGES.md](https://github.com/developmentseed/starlette-cramjam/blob/master/CHANGES.md).

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/starlette-cramjam/blob/master/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com/developmentseed/starlette-cramjam/blob/master/LICENSE)

## Authors

Created by [Development Seed](<http://developmentseed.org>)

See [contributors](https://github.com/developmentseed/starlette-cramjam/graphs/contributors) for a listing of individual contributors.
