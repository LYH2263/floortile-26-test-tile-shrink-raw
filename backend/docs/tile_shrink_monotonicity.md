# 砖边缩小后片数不降测例说明

测例模块：`backend/app/tests/test_tile_shrink.py`
被测引擎：`app.engines.tile_math.tile_count`（同参直接触发，不经服务层落库）

## 目的

固定房间尺寸与损耗百分比，验证砖边缩小后片数不降：

1. 基准砖边先算出 `raw_count` 与 `order_count`；
2. 分别只缩小砖长、只缩小砖宽、长宽同时缩小，三组 `raw` 与 `order` 均不得低于基准；
3. 至少有一组 `raw` 相对基准**严格变大**，防止缩边幅度过小被 `ceil` 吞掉却仍判通过；
4. 砖边为零或负数时引擎必须拒绝（`ValueError`）。

核对对象是同一组房间/损耗参数下引擎返回的计算结果，不是两条落库历史记录的字段表。
任一断言失败时，错误信息会打印基准与缩小后的 `raw`、`order` 和砖边。

## 固定参数

| 参数 | 值 |
| --- | --- |
| 房间长 ROOM_L | 6.0 m |
| 房间宽 ROOM_W | 4.5 m |
| 损耗 WASTE_PCT | 8 % |

## 三组对照表

| 组别 | 砖长 (m) | 砖宽 (m) | raw_count | order_count | 相对基准 raw | 相对基准 order |
| --- | --- | --- | --- | --- | --- | --- |
| 基准 | 0.6 | 0.6 | 75 | 81 | — | — |
| 只缩小砖长 | 0.5 | 0.6 | 90 | 98 | +15（严格变大） | +17 |
| 只缩小砖宽 | 0.6 | 0.5 | 90 | 98 | +15（严格变大） | +17 |
| 长宽同时缩小 | 0.5 | 0.5 | 108 | 117 | +33（严格变大） | +36 |

三组 `raw` 均严格大于基准，满足"至少一组严格变大"且留有裕量；
`order` 随 `raw` 同步不降。

## 非法砖边拒绝

| 砖长 (m) | 砖宽 (m) | 期望 |
| --- | --- | --- |
| 0.0 | 0.6 | ValueError |
| 0.6 | 0.0 | ValueError |
| -0.6 | 0.6 | ValueError |
| 0.6 | -0.6 | ValueError |

## 运行

```bash
cd backend
python -m pytest app/tests/test_tile_shrink.py
```

已有引擎片数断言（`app/tests/test_calc.py`、`app/tests/test_tile_math.py`，
含网格乘积 `cols × rows = grid_count` 测例）保持原样，未改动。
