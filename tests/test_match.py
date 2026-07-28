from seqprior import match


def _find(results, anum):
    for r in results:
        if r.anum == anum:
            return r
    return None


def test_identity_match_catalan(tiny_index):
    results = match([1, 1, 2, 5, 14, 42, 132, 429], index_path=tiny_index)
    hit = _find(results, "A000108")
    assert hit is not None
    assert hit.transform == "identity"
    assert hit.confidence == "high"


def test_offset_shift_surfaces_catalan(tiny_index):
    # Missing the leading 1,1 -- a query that starts mid-sequence.
    results = match([2, 5, 14, 42, 132], index_path=tiny_index)
    hit = _find(results, "A000108")
    assert hit is not None
    assert hit.transform == "offset"


def test_diff1_transform_finds_natural_numbers(tiny_index):
    triangular_prefix = [0, 1, 3, 6, 10, 15, 21, 28]
    results = match(triangular_prefix, index_path=tiny_index)
    hit = _find(results, "A000027")
    assert hit is not None
    assert hit.transform == "diff1"


def test_partial_sums_transform_finds_triangular(tiny_index):
    natural_prefix = [1, 2, 3, 4, 5, 6, 7, 8]
    results = match(natural_prefix, index_path=tiny_index)
    hit = _find(results, "A000217")
    assert hit is not None
    assert hit.transform == "partial_sums"


def test_scale_div2_transform_high_confidence(tiny_index):
    doubled_naturals = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    results = match(doubled_naturals, index_path=tiny_index)
    hit = _find(results, "A000027")
    assert hit is not None
    assert hit.transform == "scale_div2"
    assert hit.confidence == "high"


def test_no_match_for_random_noise(tiny_index):
    noise = [837412, 293847, 918273, 445566, 102938]
    results = match(noise, index_path=tiny_index)
    assert results == []


def test_empty_query_returns_no_results(tiny_index):
    assert match([], index_path=tiny_index) == []


def test_results_ranked_best_first(tiny_index):
    results = match([1, 1, 2, 5, 14, 42, 132, 429], index_path=tiny_index)
    confidences = [{"high": 2, "medium": 1, "low": 0}[r.confidence] for r in results]
    assert confidences == sorted(confidences, reverse=True)
