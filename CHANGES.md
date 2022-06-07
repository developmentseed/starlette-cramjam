
## 0.3.0 (TBD)

- add `compression` parameter to define compression backend and order of preference
- defaults to `gzip` -> `deflate` -> `br` order of preference (instead of `br` -> `gzip` -> `deflate`)
- remove `exclude_encoder` parameter **breaking**
- allow encoding `quality` values (e.g `gzip;0.9, deflate;0.2`)

## 0.2.0 (2022-06-03)

- switch to `pyproject.toml`
- move version definition to `starlette_cramjam.__version__`
- Add `exclude_encoder` parameter (author @drnextgis, https://github.com/developmentseed/starlette-cramjam/pull/4)

## 0.1.0 (2021-09-17)

- No change since alpha release

## 0.1.0.a0 (2021-09-08)

- Initial release.
