# srcset

Parse, build, check and resolve the HTML `srcset` and `sizes` attributes with the WHATWG
algorithms, checked against the web-platform-tests cases browsers run: which candidates
survive, what layout width `sizes` gives, and which image a browser fetches for a viewport
and a device pixel ratio.

## Install

```
pip install srcset
```

Python 3.10 or newer, no dependencies.

## Usage

Parse a `srcset` value into typed candidates. Invalid candidates are dropped, as browsers
drop them, and a comma inside a URL (a data URI, for example) does not split the list:

```python
from srcset import Candidate, build, parse

candidates = parse("small.png 1x, large.png 2x, data:image/png;base64,iVBO 3x")
print([c.url for c in candidates])
# ['small.png', 'large.png', 'data:image/png;base64,iVBO']
print(parse("hero.jpg 800w, bad.jpg 1.x"))
# [Candidate(url='hero.jpg', width=800, density=None, height=None)]
print(build([Candidate("a.png", 320), ("b.png", "2x")]))
# a.png 320w, b.png 2x
```

Resolve `sizes` and pick the image a browser would load:

```python
from srcset import Environment, parse_sizes, select

phone = Environment(width=390, height=844, density=3)
sizes = "(min-width: 1024px) 33vw, calc(100vw - 2rem)"
print(parse_sizes(sizes, phone))
# 358.0
srcset = "s.jpg 480w, m.jpg 960w, l.jpg 1440w"
print(select(srcset, phone, sizes=sizes))
# ImageSource(url='l.jpg', density=4.022346368715084)
print(select(srcset, Environment(width=1440), sizes=sizes).url)
# s.jpg
```

Check what authors wrote:

```python
from srcset import validate

for issue in validate("a.jpg 400w, b.jpg 400w, c.jpg 2x", sizes="100vw"):
    print(issue.code)
# duplicate-width
# mixed-descriptors
# sizes-without-width
```

## Command line

```
$ srcset parse "a.png 100w 50h, b.png 2x"
[{"url": "a.png", "width": 100, "density": null, "height": 50}, {"url": "b.png", "width": null, "density": 2.0, "height": null}]
$ srcset select "s.jpg 480w, l.jpg 1440w" --sizes "50vw" --width 1280 --dpr 2
l.jpg
$ srcset check "a.png 1x,, b.png 1x"
extra-comma: a comma with no image candidate before it
duplicate-density: 2 candidates share the density 1
```

`select` takes `--sizes`, `--src`, `--width` (1280 by default), `--height`, `--dpr` and
`--json`. `check` exits with status 1 when it finds an issue. `python -m srcset` works too.

## API

| Name | What it does |
| --- | --- |
| `parse(value)` | The candidates a browser keeps, as `Candidate` values. Never raises for malformed input. |
| `build(candidates)` | Serializes `Candidate` values or `(url, descriptor)` pairs; raises `SrcsetError` for anything that would not read back the same. |
| `parse_sizes(value, environment, *, auto_width=None)` | The layout width in CSS pixels, `100vw` when no entry applies. |
| `source_set(srcset, environment, *, sizes="", src="", auto_width=None)` | Every candidate as an `ImageSource` with the density it stands for, later duplicates removed. |
| `select(srcset, environment, *, sizes="", src="", auto_width=None)` | The `ImageSource` a browser would fetch, or `None`. |
| `validate(srcset, sizes=None)` | Authoring errors as `Issue` values; `sizes=None` means the attribute is absent. |
| `Candidate(url, width=None, density=None, height=None)` | A frozen candidate; `descriptor` gives its text, such as `320w` or `1.5x`. |
| `Environment(width, height=None, density=1.0, font_size=16.0)` | Viewport size in CSS pixels, device pixel ratio and root font size. |
| `ImageSource(url, density)` | A named tuple from a normalized source set. |
| `Issue(code, message)` | A named tuple with a stable code. |
| `SrcsetError` | A `ValueError` for values that cannot be built or are out of range. Wrong types raise `TypeError`. |

## Behaviour

- **Descriptors.** A width is a valid non-negative integer above zero followed by `w`; a
  density is a valid HTML floating-point number followed by `x` (`.5x` and `1e1x` are fine,
  `1.x`, `+1x` and `1X` are not), with only ASCII digits. `0x` is kept, as browsers keep it.
  The `h` descriptor is accepted only next to a width. Two descriptors of one kind, or a
  width with a density, drop the candidate.
- **Sizes.** Entries are read with a CSS tokenizer (comments, escapes, unclosed blocks).
  Lengths cover the absolute units, `em`, `rem`, and the viewport units with their `s`, `l`
  and `d` forms. Math functions: `calc`, `min`, `max`, `clamp`, `abs`, `sign`, `round`,
  `mod`, `rem`, `hypot`, `sqrt`, `pow`, `exp` and `log`, with the constants `e` and `pi`.
  A negative literal is invalid and a negative math result becomes 0. A result that is
  infinite or not a number (division by zero, for example) makes the entry invalid, which
  is what the web-platform-tests expect from browsers. `ex`, `ch`, `cap`, `ic` and `lh` use
  fixed ratios of the font size, because the real values depend on the font. Blocks nested
  more than 32 deep make their entry invalid.
- **Media conditions.** `not`, `and`, `or`, nesting, the `min-` and `max-` forms and range
  syntax such as `(400px <= width < 800px)`, for `width`, `height`, `aspect-ratio`,
  `orientation` and `resolution` (including `infinite`). Other features, and media types such as `screen`, never
  match: the first are unknown under the three-valued logic of Media Queries 4, the second
  are not allowed in `sizes`. A height-based condition is unknown while
  `Environment.height` is `None`.
- **`auto`.** When the value is `auto` or starts with `auto,` (any ASCII case), `auto`
  stands for `auto_width` if one is given: an image that allows auto-sizes, rendered at
  that width. Otherwise it is skipped and the next entry applies.
- **Selection.** The standard leaves the final pick to the browser. `select` takes the
  lowest density that covers `environment.density`, or the highest density when none
  does; this is the usual policy and it reproduces every web-platform-tests selection
  case. Width candidates with a zero size get an infinite density.
- **Issue codes.** `empty`, `extra-comma`, `invalid-descriptor`, `duplicate-width`,
  `duplicate-density`, `zero-density`, `height-descriptor`, `mixed-descriptors`,
  `sizes-without-width`, `missing-sizes` and `invalid-sizes`.

## Why

The `srcset` syntax looks like a comma-separated list, yet a URL may contain commas, so a
naive `split(",")` corrupts it. And reading the attribute is only half the job: knowing
which file a phone downloads takes the `sizes` attribute, which is CSS (lengths, `calc`,
media conditions), and the density arithmetic that ties the two together. This library
implements the WHATWG algorithms for all three steps, typed and without dependencies, and
checks itself against the web-platform-tests cases that browsers run.

## Standards

- WHATWG HTML: parsing a srcset attribute, parsing a sizes attribute, creating and
  normalizing a source set, and the srcset and sizes authoring requirements
  (https://html.spec.whatwg.org/multipage/images.html).
- CSS Syntax 3 (https://drafts.csswg.org/css-syntax-3/) and Media Queries 4
  (https://drafts.csswg.org/mediaqueries-4/).

## Development

```
pip install -r requirements-dev.txt
python scripts/fetch_upstream.py   # optional: the web-platform-tests files
pwsh scripts/check.ps1
```

The web-platform-tests files are not part of the repository; `tests/upstream/MANIFEST.json`
records where they come from, and their tests skip until the script has fetched them.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
