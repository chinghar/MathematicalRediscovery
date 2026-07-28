"""The transform battery applied to a query sequence before index lookup.

Each transform is a function ``Sequence[int] -> list[int] | None``, returning
``None`` when it doesn't apply (e.g. not enough terms, non-divisible values).
Registered in ``TRANSFORMS`` so the matcher can iterate over all of them.
Adding a new one is a `@register(name)`-decorated function.
"""

from typing import Callable, Dict, List, Optional, Sequence

Transform = Callable[[Sequence[int]], Optional[List[int]]]

TRANSFORMS: Dict[str, Transform] = {}


def register(name: str) -> Callable[[Transform], Transform]:
    def deco(fn: Transform) -> Transform:
        TRANSFORMS[name] = fn
        return fn

    return deco


@register("identity")
def _identity(seq: Sequence[int]) -> Optional[List[int]]:
    return list(seq)


def _drop(seq: Sequence[int], n: int) -> Optional[List[int]]:
    if len(seq) <= n:
        return None
    return list(seq[n:])


@register("drop1")
def _drop1(seq: Sequence[int]) -> Optional[List[int]]:
    return _drop(seq, 1)


@register("drop2")
def _drop2(seq: Sequence[int]) -> Optional[List[int]]:
    return _drop(seq, 2)


@register("drop3")
def _drop3(seq: Sequence[int]) -> Optional[List[int]]:
    return _drop(seq, 3)


@register("diff1")
def _diff1(seq: Sequence[int]) -> Optional[List[int]]:
    if len(seq) < 2:
        return None
    return [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]


@register("diff2")
def _diff2(seq: Sequence[int]) -> Optional[List[int]]:
    d1 = _diff1(seq)
    if d1 is None:
        return None
    return _diff1(d1)


@register("partial_sums")
def _partial_sums(seq: Sequence[int]) -> Optional[List[int]]:
    out = []
    total = 0
    for x in seq:
        total += x
        out.append(total)
    return out


@register("partial_products")
def _partial_products(seq: Sequence[int]) -> Optional[List[int]]:
    out = []
    prod = 1
    for x in seq:
        prod *= x
        out.append(prod)
    return out


@register("bisect_even")
def _bisect_even(seq: Sequence[int]) -> Optional[List[int]]:
    if len(seq) < 4:
        return None
    return list(seq[0::2])


@register("bisect_odd")
def _bisect_odd(seq: Sequence[int]) -> Optional[List[int]]:
    if len(seq) < 4:
        return None
    return list(seq[1::2])


def _scale_mul(seq: Sequence[int], k: int) -> Optional[List[int]]:
    return [x * k for x in seq]


def _scale_div(seq: Sequence[int], k: int) -> Optional[List[int]]:
    if any(x % k != 0 for x in seq):
        return None
    return [x // k for x in seq]


for _k in (2, 3):
    register(f"scale_x{_k}")(lambda seq, k=_k: _scale_mul(seq, k))
    register(f"scale_div{_k}")(lambda seq, k=_k: _scale_div(seq, k))
del _k


@register("plus1")
def _plus1(seq: Sequence[int]) -> Optional[List[int]]:
    return [x + 1 for x in seq]


@register("minus1")
def _minus1(seq: Sequence[int]) -> Optional[List[int]]:
    return [x - 1 for x in seq]


@register("plus_n")
def _plus_n(seq: Sequence[int]) -> Optional[List[int]]:
    return [x + i for i, x in enumerate(seq)]


@register("minus_n")
def _minus_n(seq: Sequence[int]) -> Optional[List[int]]:
    return [x - i for i, x in enumerate(seq)]


@register("abs")
def _abs(seq: Sequence[int]) -> Optional[List[int]]:
    return [abs(x) for x in seq]


@register("negate")
def _negate(seq: Sequence[int]) -> Optional[List[int]]:
    return [-x for x in seq]


@register("alt_sign")
def _alt_sign(seq: Sequence[int]) -> Optional[List[int]]:
    return [x if i % 2 == 0 else -x for i, x in enumerate(seq)]
