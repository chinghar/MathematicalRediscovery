from seqprior import keying


def test_strip_leading_ambiguous_drops_leading_zero_one_run():
    assert keying.strip_leading_ambiguous([1, 1, 2, 5, 14]) == [2, 5, 14]


def test_strip_leading_ambiguous_keeps_at_least_one_term():
    assert keying.strip_leading_ambiguous([0, 0, 0]) == [0]


def test_strip_leading_ambiguous_noop_when_first_term_not_ambiguous():
    assert keying.strip_leading_ambiguous([5, 1, 2]) == [5, 1, 2]


def test_canonical_key_strips_and_caps_length():
    terms = [1, 1, 2, 5, 14, 42, 132, 429, 1430]
    key, length = keying.canonical_key(terms)
    assert key == "2,5,14,42,132,429,1430"
    assert length == 7


def test_canonical_key_caps_at_max_terms():
    terms = list(range(2, 20))
    key, length = keying.canonical_key(terms)
    assert length == keying.MAX_KEY_TERMS
    assert key == ",".join(str(x) for x in range(2, 2 + keying.MAX_KEY_TERMS))
