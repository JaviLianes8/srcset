# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- `parse` reads a srcset attribute into a list of `Candidate` values, following the
  WHATWG splitting algorithm so URLs that contain commas stay intact.
- `build` serialises candidates back into a srcset value and rejects anything that
  cannot round-trip (empty URLs, whitespace in a URL, a trailing comma, bad descriptors).
- `Candidate` named tuple and `SrcsetError` are part of the public surface.
