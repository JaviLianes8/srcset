# srcset improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: WHATWG HTML srcset, sizes and selection; CSS Syntax 3; MQ4; WPT
- [x] Exact WHATWG srcset parser with typed candidates (w, x and the future-compat h)
- [x] Safe builder that round-trips through the parser
- [x] Conformance checker for authors (`validate`)
- [x] Sizes: CSS tokenizer, component values, lengths, math functions, media conditions
- [x] Selection: source set, density normalization, deduplication, choice for a DPR
- [x] Command line
- [x] Contracts: WPT corpus (local), cited vectors, README examples run, typing
- [x] Docs and packaging: README, CHANGELOG, metadata, installed-wheel e2e test
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Mutation run: removing guarded logic makes the suite fail
- [x] Independent review findings fixed with regression tests
- [x] Pull request opened (#2), guard clean

## Starting point

`0.1.0` gives `parse`, `build`, a `Candidate(url, descriptor)` tuple and `SrcsetError`.
Compared with the current standard:

- Number syntax is wrong in both directions. `1.x` is accepted (not a valid floating-point
  number), `0x` and `-0x` are dropped (the algorithm keeps them, only a result below zero is
  an error), and `\d` matches non-ASCII digits, so `\u0661x` passes as a density.
- The `h` descriptor is unknown: `a.png 100w 50h` is a valid candidate in every browser and
  the parser drops it.
- Descriptors come back as text, so callers re-parse `"320w"` themselves.
- Nothing reads `sizes`, nothing turns a source set into densities, and nothing answers the
  question the attribute exists for: which image does a browser fetch for this viewport and
  device pixel ratio.
- Nothing helps authors: duplicate widths, mixed `w` and `x`, `sizes` with density
  candidates and stray commas all pass silently.
- `build` accepts a URL that starts with a comma, which the parser then eats.

## Sources (fetched 2026-10-13)

- WHATWG HTML, https://html.spec.whatwg.org/multipage/images.html (whatwg/html commit
  98753fa0c3f46b6991de5544fa7207e904568892, "Last Updated 13 October 2026"): 4.8.4.2.1 srcset
  attributes (authoring rules), 4.8.4.2.2 sizes attributes, 4.8.4.3.7 selecting an image
  source, 4.8.4.3.8 creating a source set, 4.8.4.3.10 parsing a srcset attribute,
  4.8.4.3.11 parsing a sizes attribute, 4.8.4.3.12 normalizing the source densities.
- WHATWG HTML, https://html.spec.whatwg.org/multipage/common-microsyntaxes.html: valid
  non-negative integer, valid floating-point number, and the rules for parsing them.
- CSS Syntax 3, https://drafts.csswg.org/css-syntax-3/: tokenization, component values,
  parsing a comma-separated list of component values.
- Media Queries 4, https://drafts.csswg.org/mediaqueries-4/: the `<media-condition>`
  grammar, `<general-enclosed>`, Kleene three-valued evaluation, range syntax.
- web-platform-tests at commit d80fedd035bb0b03e1226efb30eebec73914d1c0 (BSD-3-Clause):
  `html/semantics/embedded-content/the-img-element/srcset/parse-a-srcset-attribute.html`,
  `.../srcset/select-an-image-source.html` and `.../sizes/support/sizes-iframed.sub.html`.
  Not committed (owner policy: no third-party text or data in the repository):
  `tests/upstream/MANIFEST.json` records URL, revision, size, sha256 and licence,
  `scripts/fetch_upstream.py` fetches and checks them into the ignored `tests/upstream/`
  folder, and their tests skip while they are absent.

## Ranked improvements

1. **Exact parser.** The splitting loop, descriptor tokenizer and descriptor parser step by
   step: HTML number microsyntaxes in ASCII only, `0x` and `-0x` kept, `1.x`, `+1x`, `1e0w`
   dropped, `h` accepted only next to `w`, overflow to infinity treated as an error.
2. **Typed candidates.** `Candidate(url, width=None, density=None, height=None)`, frozen and
   validated, with a `descriptor` property that serializes it. Breaking for 0.1.0, which was
   never published.
3. **Sizes.** `parse_sizes(value, environment)` follows the HTML algorithm on top of a real
   CSS tokenizer (comments, escapes, blocks, unclosed functions), absolute, font and
   viewport lengths, the CSS math functions, and media conditions with `not`, `and`,
   `or`, range syntax and three-valued logic. `auto` resolves when the caller passes a width.
4. **Selection.** `source_set` creates and normalizes the source set (with the `src`
   fallback), drops later duplicates; `select` picks the smallest density that covers the
   device pixel ratio, else the densest, which is what browsers do in practice.
5. **Conformance checker.** `validate(srcset, sizes=None)` lists authoring errors with stable
   codes: extra commas, dropped candidates, duplicates, mixed descriptors, `sizes` without
   widths, zero density, the `h` descriptor, invalid source size lists.
6. **Safe builder.** `build` accepts candidates or `(url, descriptor)` pairs and refuses
   anything the parser would read differently: URLs with whitespace or edge commas,
   descriptor combinations the parser drops. `parse(build(x)) == x` is a tested property.
7. **Command line.** `srcset parse|select|check` (also `python -m srcset`): JSON out for
   scripts, a non-zero exit from `check` for linting templates.
8. **Ground truth contracts.** Every WPT srcset parsing and selection case, every WPT sizes
   case grouped by its reference, cited spec vectors, executed README examples, a mypy
   check of the public types, and an installed-wheel test.

## Out of scope

- `<picture>` and `<source media type>`: media query lists with media types and MIME type
  support are the caller's job; the media condition engine covers `sizes`.
- Font metrics: `ex`, `ch`, `cap`, `ic` and `lh` use fixed ratios of the font size, since
  the real values depend on the font.
- Trigonometric math functions: they need angle types, which never yield a length here.
- URL resolution against a base URL: candidates keep the attribute's text.

## Verification

- Gates on CPython 3.14 (a clean clone): `ruff format --check .`, `ruff check .`,
  `mypy --strict src` (and `src tests`) and `pytest`, all exit 0. With `SRCSET_E2E=1` the
  installed-wheel test builds the wheel and sdist, checks their contents (no fetched files,
  no planning notes, the console script entry point), installs the wheel in a fresh venv and
  drives the API, the `srcset` command and `python -m srcset` from an empty folder.
- Ground truth: every web-platform-tests case passes. 236 `<img>` cases from
  `parse-a-srcset-attribute.html` and `select-an-image-source.html` give the image a
  browser shows, and 179 sizes cases from `sizes-iframed.sub.html` pick the same image as
  their reference, with the references themselves checked (small image for the `1px`
  paragraph, large one for the `100vw` paragraphs). Without the fetched files they skip.
- Mutation runs (AST mutations of comparisons, boolean operators, arithmetic, constants,
  `if` tests, `raise`, `continue` and `return`; no bytecode, `__pycache__` purged, a
  timeout per mutant, baseline green before and after). The last run made 1659 mutants;
  64 survived and were read one by one. Two were killed by new grammar tests. The rest
  are equivalent: type guards whose absence still raises `TypeError` a step later,
  `zip(strict=...)` on lists that always match, position bumps at end of input, bounds
  that no input can reach (surrogates are replaced before tokenizing, tabs and spaces never
  reach the url non-printable check), the digit chunk size, and branches whose fallback
  gives the same unknown result. Earlier runs led to the boundary tests in
  `test_media.py`, `test_css_boundaries.py` and `test_edges.py`, and to removing two dead
  guards.

## Review fixes

An independent review attacked the branch. Each finding below is fixed and has a test in
`tests/test_review_regressions.py` that fails on the code before the fix:

- Widths and heights longer than the interpreter's digit limit raised `ValueError`; they
  now parse and serialize exactly (chunked conversion).
- Nesting 500 blocks deep raised `RecursionError`; blocks deeper than 32 are skipped and
  make their entry invalid.
- Huge widths overflowed in `select`, `validate` and `Candidate(density=10**400)`; they give
  an infinite density, a readable message and `SrcsetError`.
- `auto` was resolved anywhere in the list; it now needs the value to be `auto` or start
  with `auto,`, the "allows auto-sizes" rule, and `validate` checks the same.
- `validate` missed a comma after the last candidate.
- Only `calc`, `min`, `max` and `clamp` were accepted; `abs`, `sign`, `round`, `mod`,
  `rem`, `hypot`, `sqrt`, `pow`, `exp`, `log`, `e` and `pi` work now.
- Negative resolutions were unknown instead of false in the negative range; `infinite` is
  accepted.
- The command line crashed on a legacy console code page; output now escapes what the
  console cannot encode, and JSON is ASCII.
- `validate` accepted `<general-enclosed>` and `min-`/`max-` prefixes outside the plain
  form.
- Ident code points follow the current CSS Syntax ranges.
- A test that accepted two outcomes now pins one; `hatchling>=1.27` is required.
- Not changed: an infinite or NaN math result keeps the entry invalid, because the
  web-platform-tests sizes cases expect `calc(1px / 0)` to fall back like an invalid entry.
