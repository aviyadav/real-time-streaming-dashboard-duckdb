from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import polars as pl


class ParquetWriter:
    def __init__(self, parquet_root: str, subdir: str) -> None:
        self.parquet_root = parquet_root
        self.subdir = subdir

    def write(self, df: pl.DataFrame, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"part-{uuid4().hex}.parquet"
        out_path = out_dir / fname

        # Polars parquet write
        df.write_parquet(str(out_path), compression="zstd")
        return out_path