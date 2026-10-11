# srcset

Parse and build the HTML `srcset` attribute with width and pixel-density descriptors.

## Install

```
pip install srcset
```

## Usage

```python
from srcset import parse, build, Candidate

candidates = parse("small.png 1x, large.png 2x")
# [Candidate(url='small.png', descriptor='1x'),
#  Candidate(url='large.png', descriptor='2x')]

parse("a.png 320w, b.png 640w")
# [Candidate(url='a.png', descriptor='320w'),
#  Candidate(url='b.png', descriptor='640w')]

# A URL may contain commas; only separating commas split the list.
parse("data:image/png;base64,iVBORw0KGgo 1x, next.png 2x")
# [Candidate(url='data:image/png;base64,iVBORw0KGgo', descriptor='1x'),
#  Candidate(url='next.png', descriptor='2x')]

build([("a.png", "320w"), ("b.png", "640w"), Candidate("c.png", "2x")])
# 'a.png 320w, b.png 640w, c.png 2x'
```

`parse` returns a list of `Candidate` named tuples (`url`, `descriptor`). A candidate
with no descriptor has an empty `descriptor`. Candidates with an invalid or ambiguous
descriptor are dropped, matching how a browser reads the attribute. `build` is the
inverse and raises `SrcsetError` on input it cannot represent: an empty URL, a URL that
contains whitespace or ends with a comma, or a descriptor that is neither a width
(`320w`) nor a density (`2x`).

## Why

The `srcset` syntax is deceptively awkward: candidates are comma-separated, yet a URL
(a data URI, for example) may itself contain commas, so a naive `split(",")` corrupts
the list. The WHATWG specification resolves this by reading each URL as a run of
non-whitespace and tokenising descriptors separately. No maintained Python package
ships that algorithm: Rust, JavaScript and Go have faithful ports, while Python users
hand-roll it on top of an HTML parser. This library is a small, typed, zero-dependency
implementation that both reads and writes the attribute.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
