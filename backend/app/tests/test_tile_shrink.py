"""砖边缩小后片数不降:shrinking tile edges must never lower raw/order counts.

固定房间与损耗,基准砖边先算 raw_count/order_count,再分三组缩边
(只缩砖长、只缩砖宽、长宽同时缩),逐一断言不降;且至少一组 raw 严格
变大,防止缩边幅度过小被 ceil 吞掉仍判通过。砖边为零或负数必须拒绝。

核对对象是同参调用引擎 tile_count 的计算结果,不涉及落库记录。
"""

import pytest

from app.engines.tile_math import tile_count

ROOM_L = 6.0
ROOM_W = 4.5
WASTE_PCT = 8.0

BASE_TILE_L = 0.60
BASE_TILE_W = 0.60
SHRINK_TILE_L = 0.55
SHRINK_TILE_W = 0.50


def _counts(tile_l, tile_w):
    r = tile_count(ROOM_L, ROOM_W, tile_l, tile_w, WASTE_PCT)
    return r["raw_count"], r["order_count"]


def _baseline():
    return _counts(BASE_TILE_L, BASE_TILE_W)


def _fail_msg(tag, tile_l, tile_w, base_raw, base_order, raw, order):
    return (
        f"{tag} 片数不降被破坏: "
        f"基准(tile_l={BASE_TILE_L}, tile_w={BASE_TILE_W}) "
        f"raw={base_raw} order={base_order} | "
        f"缩边后(tile_l={tile_l}, tile_w={tile_w}) raw={raw} order={order}"
    )


def _assert_not_less(tag, tile_l, tile_w):
    base_raw, base_order = _baseline()
    raw, order = _counts(tile_l, tile_w)
    msg = _fail_msg(tag, tile_l, tile_w, base_raw, base_order, raw, order)
    assert raw >= base_raw, msg
    assert order >= base_order, msg
    return raw, order


def test_shrink_length_only_not_less():
    _assert_not_less("只缩砖长", SHRINK_TILE_L, BASE_TILE_W)


def test_shrink_width_only_not_less():
    _assert_not_less("只缩砖宽", BASE_TILE_L, SHRINK_TILE_W)


def test_shrink_both_edges_not_less():
    _assert_not_less("长宽同时缩", SHRINK_TILE_L, SHRINK_TILE_W)


def test_at_least_one_group_raw_strictly_increases():
    base_raw, base_order = _baseline()
    groups = [
        ("只缩砖长", SHRINK_TILE_L, BASE_TILE_W),
        ("只缩砖宽", BASE_TILE_L, SHRINK_TILE_W),
        ("长宽同时缩", SHRINK_TILE_L, SHRINK_TILE_W),
    ]
    results = [(tag, tl, tw, *_counts(tl, tw)) for tag, tl, tw in groups]
    lines = [
        _fail_msg(tag, tl, tw, base_raw, base_order, raw, order)
        for tag, tl, tw, raw, order in results
    ]
    assert any(raw > base_raw for _, _, _, raw, _ in results), (
        "三组缩边 raw 均未严格变大,缩边幅度可能被 ceil 吞掉:\n" + "\n".join(lines)
    )


@pytest.mark.parametrize(
    "tile_l,tile_w",
    [
        (0.0, BASE_TILE_W),
        (BASE_TILE_L, 0.0),
        (0.0, 0.0),
        (-0.60, BASE_TILE_W),
        (BASE_TILE_L, -0.50),
        (-SHRINK_TILE_L, -SHRINK_TILE_W),
    ],
)
def test_zero_or_negative_tile_edge_rejected(tile_l, tile_w):
    with pytest.raises(ValueError):
        tile_count(ROOM_L, ROOM_W, tile_l, tile_w, WASTE_PCT)
