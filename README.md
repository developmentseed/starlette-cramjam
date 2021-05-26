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

```python

import uvicorn

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

from starlette_cramjam import CompressionMiddleware

# create application
app = Starlette()

# register the CompressionMiddleware
app.add_middleware(CompressionMiddleware)


@app.route("/")
def index(request):
    return PlainTextResponse("Hello World")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

```
