from seqprior.transforms import TRANSFORMS


def test_registry_has_expected_transforms():
    expected = {
        "identity", "drop1", "drop2", "drop3",
        "diff1", "diff2",
        "partial_sums", "partial_products",
        "bisect_even", "bisect_odd",
        "scale_x2", "scale_x3", "scale_div2", "scale_div3",
        "plus1", "minus1", "plus_n", "minus_n",
        "abs", "negate", "alt_sign",
    }
    assert expected <= set(TRANSFORMS.keys())


def test_identity():
    assert TRANSFORMS["identity"]([1, 2, 3]) == [1, 2, 3]


def test_drop1():
    assert TRANSFORMS["drop1"]([1, 2, 3, 4]) == [2, 3, 4]
    assert TRANSFORMS["drop1"]([1]) is None


def test_drop2():
    assert TRANSFORMS["drop2"]([1, 2, 3, 4]) == [3, 4]
    assert TRANSFORMS["drop2"]([1, 2]) is None


def test_drop3():
    assert TRANSFORMS["drop3"]([1, 2, 3, 4]) == [4]
    assert TRANSFORMS["drop3"]([1, 2, 3]) is None


def test_diff1():
    assert TRANSFORMS["diff1"]([1, 3, 6, 10]) == [2, 3, 4]
    assert TRANSFORMS["diff1"]([5]) is None


def test_diff2():
    assert TRANSFORMS["diff2"]([1, 3, 6, 10, 15]) == [1, 1, 1]
    assert TRANSFORMS["diff2"]([1, 2]) is None


def test_partial_sums():
    assert TRANSFORMS["partial_sums"]([1, 2, 3, 4]) == [1, 3, 6, 10]


def test_partial_products():
    assert TRANSFORMS["partial_products"]([1, 2, 3, 4]) == [1, 2, 6, 24]


def test_bisect_even():
    assert TRANSFORMS["bisect_even"]([1, 2, 3, 4, 5, 6]) == [1, 3, 5]
    assert TRANSFORMS["bisect_even"]([1, 2, 3]) is None


def test_bisect_odd():
    assert TRANSFORMS["bisect_odd"]([1, 2, 3, 4, 5, 6]) == [2, 4, 6]
    assert TRANSFORMS["bisect_odd"]([1, 2, 3]) is None


def test_scale_x2():
    assert TRANSFORMS["scale_x2"]([1, 2, 3]) == [2, 4, 6]


def test_scale_x3():
    assert TRANSFORMS["scale_x3"]([1, 2, 3]) == [3, 6, 9]


def test_scale_div2():
    assert TRANSFORMS["scale_div2"]([2, 4, 6]) == [1, 2, 3]
    assert TRANSFORMS["scale_div2"]([1, 2, 3]) is None


def test_scale_div3():
    assert TRANSFORMS["scale_div3"]([3, 6, 9]) == [1, 2, 3]
    assert TRANSFORMS["scale_div3"]([1, 2, 3]) is None


def test_plus1():
    assert TRANSFORMS["plus1"]([1, 2, 3]) == [2, 3, 4]


def test_minus1():
    assert TRANSFORMS["minus1"]([1, 2, 3]) == [0, 1, 2]


def test_plus_n():
    assert TRANSFORMS["plus_n"]([1, 1, 1, 1]) == [1, 2, 3, 4]


def test_minus_n():
    assert TRANSFORMS["minus_n"]([1, 2, 3, 4]) == [1, 1, 1, 1]


def test_abs():
    assert TRANSFORMS["abs"]([-1, 2, -3]) == [1, 2, 3]


def test_negate():
    assert TRANSFORMS["negate"]([1, -2, 3]) == [-1, 2, -3]


def test_alt_sign():
    assert TRANSFORMS["alt_sign"]([1, 2, 3, 4]) == [1, -2, 3, -4]
