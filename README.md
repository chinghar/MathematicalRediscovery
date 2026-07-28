# seqprior

Offline prior-art search for integer sequences against the [OEIS](https://oeis.org)
bulk data. Given a sequence, `seqprior` applies a battery of simple transforms
(offsets, differences, partial sums, scaling, sign changes, ...) and reports
which known OEIS entries turn up — so you can sanity-check "is this sequence
already known?" before claiming it's new, without waiting on OEIS's
email-only, rate-limited [Superseeker](https://oeis.org/superhelp.txt) service.

<!-- TODO: replace with a real terminal recording, e.g. `seqprior match "1,1,2,5,14,42,132,429"` -->
> 🎞️ *[demo GIF placeholder]*

## Prior art

This is **not a novel algorithm**. It's a small, local reimplementation of the
matching idea behind OEIS's own
[Superseeker](https://oeis.org/superhelp.txt) tool: try a bunch of standard
transforms on a query sequence and look each result up against the database.
Superseeker does much more (generating functions, Euler/Möbius transforms,
`gf-invert`, ...) and is the authoritative tool if you have the time to wait
for its email reply. `seqprior` exists because Superseeker isn't scriptable
and isn't offline — this trades sophistication for speed and repeatability
when triaging a large batch of candidate sequences (its original motivation:
checking sequences from the [erdosproblems.com](https://erdosproblems.com) ↔
OEIS crowdsourcing project).

## Install

```bash
git clone <this-repo>
cd seqprior
pip install -e .
```

Requires Python 3.11+. The only runtime dependency is `requests`.

## Usage

```bash
# One-time: download OEIS's bulk data and build a local index (~40MB download).
seqprior fetch

# Look up a sequence.
seqprior match "1,1,2,5,14,42,132,429"
# A000108     high        identity      overlap=8  Number of Dyck paths of...

# Works even if your sequence starts partway through a known one.
seqprior match "2,5,14,42,132"
# A000108     medium      offset        overlap=5  Number of Dyck paths of...

# Run the evaluation harness (writes benchmark/results.md).
seqprior benchmark
```

As a library:

```python
from seqprior import match

for r in match([1, 2, 5, 14, 42]):
    print(r.anum, r.confidence, r.transform, r.name)
```

## Output contract

`seqprior` never prints a binary "novel" / "known" verdict. It prints a
ranked list of candidates, each tagged with a confidence band (`high` /
`medium` / `low`) and the transform that produced it, or:

```
No match found. This is weak evidence, not proof of novelty.
```

The tool is deliberately calibrated **toward false positives**: a wrong
"novel" claim (missing a sequence that's actually in OEIS) is worse than
being shown a wrong or low-confidence candidate, because the latter is easy
to dismiss on inspection while the former can lead to a false novelty claim.
So every hit the matcher finds is surfaced, with an honest confidence label,
rather than being filtered down to a single yes/no answer. See
`benchmark/results.md` for the actual precision/recall/specificity numbers
this calibration produces.

## How matching works

1. Terms are normalized to a canonical key: a leading run of ambiguous 0/1
   values is stripped (many OEIS sequences share these and they carry little
   signal), and the first 8 remaining terms are joined into a string key.
2. The same battery of transforms is applied to the *query* — identity,
   offset shifts, first/second differences, partial sums/products, even/odd
   bisection, scaling by small constants, ±1, ±n, absolute value, and sign
   reversal (see `seqprior/transforms.py`; adding one is ~10 lines).
3. Each transformed result's canonical key is looked up in a local SQLite
   index built from OEIS's bulk files.
4. Candidates are re-verified against the full stored terms (not just the
   8-term key) to rule out short-key collisions, then ranked by how much
   overlap survived verification and how trustworthy the transform is
   (an exact `identity` hit is stronger evidence than a `bisect_even` hit,
   which threw away half the sequence before comparing).

Not implemented (out of scope for v1): generating-function transforms,
Euler/Möbius transforms, and anything beyond integer-sequence matching
(no text/conjecture search).

## Data source and license

`seqprior fetch` downloads `stripped.gz` and `names.gz` from
<https://oeis.org/> — the bulk files documented at
<https://oeis.org/wiki/Download>. OEIS content is licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); see
<https://oeis.org/wiki/The_OEIS_End-User_License_Agreement>. This project's
own code is MIT-licensed, but **OEIS data itself is not redistributed** —
it's cached locally on your machine (outside the repo, see `SEQPRIOR_CACHE`)
and never committed to git. If you publish results derived from this data,
attribute "The Online Encyclopedia of Integer Sequences" with a link to
<https://oeis.org/> or the relevant `A`-number page.

## Benchmark

`seqprior benchmark` is a reproducible (fixed-seed) evaluation harness:

- **Recall**: samples real OEIS sequences from the local index, applies a
  ground-truth transform to build a synthetic query, and checks whether
  `match()` recovers the original A-number — broken out per transform, so
  weak transforms (e.g. lossy ones like bisection with no inverse in the
  registry) are visible rather than averaged away.
- **Specificity**: feeds random noise sequences through the matcher and
  checks that it reports no match.
- Both feed a confusion matrix (precision/recall/specificity) written to
  `benchmark/results.md` along with the seed used, so the run is
  reproducible.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Cache location

By default, downloaded data and the built index live in `~/.cache/seqprior`.
Override with the `SEQPRIOR_CACHE` environment variable.
