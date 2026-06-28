from __future__ import annotations

from pathlib import Path


def parquet_partition_path(root: str, subdir: str, pair: str, trade_date: str, hour: str) -> Path:
    """
    <root>/<subdir>/pair=BTCUSDT/trade_date=YYYY-MM-DD/hour=HH/
    """
    return Path(root) / subdir / f"pair={pair}" / f"trade_date={trade_date}" / f"hour={hour}"