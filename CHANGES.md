## 0.4.0 (2024-10-17)

- add `compression_level` option
- update `cramjam` version limit to `cramjam>=2.4,<2.10`

## 0.3.3 (2024-05-24)

- add python 3.12 and update pyrus-cramjam version dependency

## 0.3.2 (2022-10-28)

- add python 3.11 and update pyrus-cramjam version dependency

## 0.3.1 (2022-09-08)

- update `pyrus-cramjam` version requirement to allow `2.5.0`

## 0.3.0 (2022-06-07)

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
