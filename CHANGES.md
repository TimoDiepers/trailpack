# `trailpack` Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-09-22

### Fixed

* `StandardValidator()` raised `FileNotFoundError: Standard version v1.0.0 not
  found. Available versions: []` on every installed copy of trailpack.
  `validation/standards/*.yaml` was never included in the wheel or the sdist, so
  there was no standard to validate against unless you ran from a source
  checkout.
* The 0.2.0 release shipped none of the subpackages, so `trailpack.packing` and
  `trailpack.validation` could not be imported at all from PyPI. Fixed on `main`
  in fb7ee0f, released here for the first time.
* `MetaDataBuilder.set_dates()` wrote a full ISO timestamp, but the standard
  specifies `created` as `YYYY-MM-DD` and validates it against that pattern.
  Every package the builder produced failed its own validation.
* The schema check rejected pandas 3's default `str` dtype for string columns,
  reporting valid data as a type mismatch.

### Changed

* README: fixed the PyPI status link, removed the Codecov badge, made the
  installation commands copyable.

## [0.2.0] - 2025-10-17
* First working version

## [0.1.0] - 2025-10-14
* Initial release

### Added

### Changed

### Removed
