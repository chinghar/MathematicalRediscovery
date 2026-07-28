# seqprior benchmark results

- Seed: `42`
- Index size at run time: 397,840 sequences
- Runtime: 135.0s
- Method: sample real OEIS sequences, apply one transform to produce a synthetic query, and check whether `match()` recovers the original A-number at rank 1 (recall@1) and within the top 5 (recall@5). A separate negative track feeds random noise sequences through the matcher and checks that it reports no match.

## Recall per transform (ground-truth transform applied to a known sequence)

| Transform | Attempted | Skipped (n/a) | Recall@1 | Recall@5 |
|---|---:|---:|---:|---:|
| identity | 19 | 0 | 84% | 89% |
| drop1 | 19 | 0 | 47% | 58% |
| drop2 | 19 | 0 | 32% | 37% |
| drop3 | 19 | 0 | 5% | 11% |
| diff1 | 19 | 0 | 5% | 5% |
| diff2 | 19 | 0 | 0% | 0% |
| partial_sums | 19 | 0 | 21% | 32% |
| partial_products | 19 | 0 | 0% | 0% |
| bisect_even | 19 | 0 | 0% | 0% |
| bisect_odd | 19 | 0 | 0% | 0% |
| scale_x2 | 19 | 0 | 89% | 100% |
| scale_div2 | 0 | 19 | 0% | 0% |
| scale_x3 | 19 | 0 | 100% | 100% |
| scale_div3 | 1 | 18 | 100% | 100% |
| plus1 | 19 | 0 | 89% | 100% |
| minus1 | 19 | 0 | 100% | 100% |
| plus_n | 19 | 0 | 84% | 95% |
| minus_n | 19 | 0 | 95% | 95% |
| abs | 19 | 0 | 74% | 89% |
| negate | 19 | 0 | 89% | 89% |
| alt_sign | 19 | 0 | 100% | 100% |

**Overall recall@1: 194/362 = 53.6%** &nbsp;&nbsp; **Overall recall@5: 210/362 = 58.0%**

Transforms that discard information to build the query (`bisect_even`, `bisect_odd`, `diff2`, `partial_products`) have no general inverse in the registry, so low recall for those rows is expected, not a bug — it's the benchmark doing its job of surfacing weak spots. `drop1`/`drop2`/`drop3` (offset shifts) only recover when the dropped terms happen to be the leading 0/1 run that the canonical key already strips; partial recall there reflects that real limitation, not a measurement error.

## Negative track (random noise, no true match expected)

- Attempted: 100
- False positives (any candidate surfaced): 0
- False positive rate: 0.0%

## Confusion matrix (top-1 prediction vs. ground truth)

| | Predicted: match | Predicted: no match |
|---|---:|---:|
| **Actually known (positive track)** | TP = 194 | FN = 168 |
| **Actually novel/noise (negative track)** | FP = 0 | TN = 100 |

- Precision: 100.0%
- Recall: 53.6%
- Specificity (true negative rate): 100.0%

Recall is intentionally prioritized over precision in the tool's design: a missed known sequence (a false 'novel') is worse than a spurious low-confidence candidate, which is why every hit is shown with a confidence band instead of being filtered to a binary yes/no.
