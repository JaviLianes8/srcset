# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added

- `parse_sizes` reads a sizes attribute with the WHATWG algorithm on top of a CSS tokenizer:
  absolute, font and viewport lengths, the CSS math functions, and media
  conditions with `not`, `and`, `or`, range syntax and three-valued logic. `auto` resolves
  to a width the caller passes when the value starts with it.
- `source_set` and `select` build and normalize the source set (with the `src` fallback)
  and pick the image a browser fetches for an `Environment` (viewport, pixel ratio, font
  size).
- `validate` lists authoring errors with stable codes.
- The `srcset` command (`parse`, `select`, `check`) and `python -m srcset`.
- Tests against the web-platform-tests srcset and sizes cases, fetched locally by
  `scripts/fetch_upstream.py`, plus executed README examples, a typing check and an
  installed-wheel test.

### Changed

- `Candidate` is a frozen, validated value with `url`, `width`, `density` and `height`;
  its `descriptor` property gives the text. It replaces the `(url, descriptor)` tuple.
- `build` also accepts `Candidate` values, normalizes descriptor text and refuses a URL
  that starts with a comma.

### Fixed

- Numbers follow the HTML microsyntaxes: `1.x` is no longer accepted, `0x` and `-0x` are
  kept, and only ASCII digits count.
- `100w 50h` is a valid candidate: the `h` descriptor is accepted next to a width.
- Widths of any length parse exactly, past the interpreter's digit limit.

## [0.1.0]

- `parse` reads a srcset attribute into a list of `Candidate` values, following the
  WHATWG splitting algorithm so URLs that contain commas stay intact.
- `build` serialises candidates back into a srcset value and rejects anything that
  cannot round-trip (empty URLs, whitespace in a URL, a trailing comma, bad descriptors).
- `Candidate` named tuple and `SrcsetError` are part of the public surface.
