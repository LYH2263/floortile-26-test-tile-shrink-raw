"""砖边缩小后片数不降测例。

固定房间尺寸与损耗百分比，基准砖边先算出 raw_count 与 order_count，
再分别只缩小砖长、只缩小砖宽、长宽同时缩小，三组 raw 与 order 均不得低于基准；
且至少有一组 raw 相对基准严格变大（防止缩边幅度过小被 ceil 吞掉仍判通过）。
砖边为零或负数须被引擎拒绝。

核对对象：同一组房间/损耗参数直接喂给引擎的同参计算结果，
不经过服务层落库，也不比对两条历史记录的字段表。
"""

from app.engines.tile_math import tile_count

# 固定房间尺寸与损耗百分比
ROOM_L = 6.0
ROOM_W = 4.5
WASTE_PCT = 8.0

# 基准砖边与三组缩边方案 (tile_l, tile_w)
BASE_TILE = (0.6, 0.6)
SHRINK_GROUPS = {
    "只缩小砖长": (0.5, 0.6),
    "只缩小砖宽": (0.6, 0.5),
    "长宽同时缩小": (0.5, 0.5),
}


def _counts(tile_l, tile_w):
    """同参触发引擎，返回 (raw_count, order_count)。"""
    r = tile_count(ROOM_L, ROOM_W, tile_l, tile_w, WASTE_PCT)
    return r["raw_count"], r["order_count"]


def _describe(tile, raw, order):
    return f"砖边 {tile[0]}x{tile[1]} -> raw={raw}, order={order}"


def _assert_not_lower(label, shrunk_tile, base_tile, base_raw, base_order):
    """单组对照：缩边后 raw 与 order 不得低于基准，失败时打印双方片数与砖边。"""
    s_raw, s_order = _counts(*shrunk_tile)
    assert s_raw >= base_raw and s_order >= base_order, (
        f"{label}后片数下降\n"
        f"  基准:   {_describe(base_tile, base_raw, base_order)}\n"
        f"  缩小后: {_describe(shrunk_tile, s_raw, s_order)}"
    )
    return s_raw, s_order


def test_shrink_tile_length_only_not_lower():
    base_raw, base_order = _counts(*BASE_TILE)
    _assert_not_lower("只缩小砖长", SHRINK_GROUPS["只缩小砖长"], BASE_TILE, base_raw, base_order)


def test_shrink_tile_width_only_not_lower():
    base_raw, base_order = _counts(*BASE_TILE)
    _assert_not_lower("只缩小砖宽", SHRINK_GROUPS["只缩小砖宽"], BASE_TILE, base_raw, base_order)


def test_shrink_both_edges_not_lower():
    base_raw, base_order = _counts(*BASE_TILE)
    _assert_not_lower("长宽同时缩小", SHRINK_GROUPS["长宽同时缩小"], BASE_TILE, base_raw, base_order)


def test_at_least_one_group_raw_strictly_greater():
    """至少一组缩边后 raw 严格大于基准，避免缩边幅度过小被 ceil 吞掉仍判通过。"""
    base_raw, base_order = _counts(*BASE_TILE)
    results = {
        label: _assert_not_lower(label, tile, BASE_TILE, base_raw, base_order)
        for label, tile in SHRINK_GROUPS.items()
    }
    strict = [label for label, (s_raw, _) in results.items() if s_raw > base_raw]
    assert strict, (
        "三组缩边 raw 均未超过基准，缩边幅度可能被 ceil 吞掉\n"
        f"  基准: {_describe(BASE_TILE, base_raw, base_order)}\n"
        + "\n".join(
            f"  {label}: {_describe(SHRINK_GROUPS[label], raw, order)}"
            for label, (raw, order) in results.items()
        )
    )


def test_zero_or_negative_tile_edge_rejected():
    """砖边为零或负数时引擎必须拒绝（ValueError）。"""
    bad_tiles = [
        ("砖长为零", (0.0, 0.6)),
        ("砖宽为零", (0.6, 0.0)),
        ("砖长为负", (-0.6, 0.6)),
        ("砖宽为负", (0.6, -0.6)),
    ]
    for label, (tile_l, tile_w) in bad_tiles:
        try:
            tile_count(ROOM_L, ROOM_W, tile_l, tile_w, WASTE_PCT)
        except ValueError:
            continue
        raise AssertionError(f"{label}未被拒绝: 砖边 {tile_l}x{tile_w}")
