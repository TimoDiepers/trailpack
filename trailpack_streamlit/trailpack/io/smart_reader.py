from pathlib import Path
from typing import Union, Optional
import pandas as pd


class SmartDataReader:
    """
    Adaptive data reader that chooses optimal technology based on file size.
    Strategy:
    - <10MB: pandas (simplicity, compatibility)
    - 10-500MB: polars (speed, memory efficiency)
    - >500MB: polars lazy (streaming, minimal memory)
    - CSV always: pyarrow or polars (much faster than pandas)
    """

    SMALL_FILE = 10 * 1024 * 1024      # 10MB
    LARGE_FILE = 500 * 1024 * 1024     # 500MB

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.file_size = self.file_path.stat().st_size
        self.engine = self._choose_engine()

    def _choose_engine(self) -> str:
        """Choose optimal engine based on file size."""
        suffix = self.file_path.suffix.lower()
        if suffix == '.csv':
            return 'polars' if self.file_size > self.SMALL_FILE else 'pyarrow'
        elif suffix in ['.xlsx', '.xlsm', '.xls']:
            if self.file_size < self.SMALL_FILE:
                return 'pandas'
            elif self.file_size < self.LARGE_FILE:
                return 'polars'
            else:
                return 'polars_lazy'
        elif suffix == '.parquet':
            return 'polars'
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def read(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Read file using optimal engine, always return pandas DataFrame.

        Args:
            sheet_name: Sheet name for Excel files (optional)

        Returns:
            pandas DataFrame with file contents

        Why pandas output?
        - Rest of codebase expects pandas
        - Can convert polars → pandas at end
        - Only final result in memory
        """
        if self.engine == 'pandas':
            return self._read_pandas(sheet_name)
        elif self.engine == 'polars':
            return self._read_polars(sheet_name)
        elif self.engine == 'polars_lazy':
            return self._read_polars_lazy(sheet_name)
        elif self.engine == 'pyarrow':
            return self._read_pyarrow()
        else:
            raise ValueError(f"Unknown engine: {self.engine}")

    def _read_pandas(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Small files: Use pandas."""
        suffix = self.file_path.suffix.lower()

        if suffix == '.csv':
            return pd.read_csv(self.file_path)
        elif suffix in ['.xlsx', '.xlsm', '.xls']:
            return pd.read_excel(self.file_path, sheet_name=sheet_name)
        elif suffix == '.parquet':
            return pd.read_parquet(self.file_path)
        else:
            raise ValueError(f"Unsupported format for pandas: {suffix}")

    def _read_polars(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Medium files: Use polars, convert to pandas."""
        try:
            import polars as pl
        except ImportError:
            # Fallback to pandas if polars not installed
            return self._read_pandas(sheet_name)

        suffix = self.file_path.suffix.lower()

        try:
            if suffix == '.csv':
                df_pl = pl.read_csv(self.file_path)
            elif suffix == '.parquet':
                df_pl = pl.read_parquet(self.file_path)
            elif suffix in ['.xlsx', '.xlsm', '.xls']:
                # Try polars Excel support (requires calamine)
                try:
                    df_pl = pl.read_excel(self.file_path, sheet_name=sheet_name)
                except Exception:
                    # Fallback to pandas if polars doesn't support
                    return self._read_pandas(sheet_name)
            else:
                raise ValueError(f"Unsupported format for polars: {suffix}")

            # Convert to pandas (only final result in memory)
            return df_pl.to_pandas()

        except Exception:
            # If anything fails, fallback to pandas
            return self._read_pandas(sheet_name)

    def _read_polars_lazy(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Large files: Use lazy evaluation, process in chunks."""
        try:
            import polars as pl
        except ImportError:
            # Fallback to pandas with chunking
            return self._read_pandas_chunked(sheet_name)

        suffix = self.file_path.suffix.lower()

        try:
            if suffix == '.csv':
                # Lazy CSV reading
                lf = pl.scan_csv(self.file_path)
                # For preview, collect first 10k rows
                df_pl = lf.head(10000).collect()
            elif suffix == '.parquet':
                # Lazy Parquet reading
                lf = pl.scan_parquet(self.file_path)
                df_pl = lf.head(10000).collect()
            elif suffix in ['.xlsx', '.xlsm', '.xls']:
                # For Excel, read in chunks with pandas
                return self._read_pandas_chunked(sheet_name)
            else:
                raise ValueError(f"Unsupported format for lazy reading: {suffix}")

            return df_pl.to_pandas()

        except Exception:
            # Fallback to pandas chunked reading
            return self._read_pandas_chunked(sheet_name)

    def _read_pandas_chunked(self, sheet_name: Optional[str] = None, chunk_size: int = 10000) -> pd.DataFrame:
        """Read large Excel files in chunks, return first chunk for preview."""
        suffix = self.file_path.suffix.lower()

        if suffix in ['.xlsx', '.xlsm', '.xls']:
            # Read first chunk only for preview
            return pd.read_excel(
                self.file_path,
                sheet_name=sheet_name,
                nrows=chunk_size
            )
        else:
            # For CSV, use pandas chunksize
            chunks = []
            for i, chunk in enumerate(pd.read_csv(self.file_path, chunksize=chunk_size)):
                chunks.append(chunk)
                if i >= 10:  # First 100k rows
                    break
            return pd.concat(chunks, ignore_index=True)

    def _read_pyarrow(self) -> pd.DataFrame:
        """CSV with PyArrow (fastest CSV reader)."""
        try:
            import pyarrow.csv as pv
            table = pv.read_csv(self.file_path)
            return table.to_pandas()
        except ImportError:
            # Fallback to pandas if pyarrow not available
            return pd.read_csv(self.file_path)

    def estimate_memory(self) -> str:
        """
        Estimate memory usage.

        Returns:
            Human-readable memory estimate string
        """
        # Rough estimate: file size * 3 (typical overhead for in-memory representation)
        estimated = self.file_size * 3

        if estimated < 1024:
            return f"{estimated:.1f} B"
        elif estimated < 1024 * 1024:
            return f"{estimated / 1024:.1f} KB"
        elif estimated < 1024 * 1024 * 1024:
            return f"{estimated / (1024 * 1024):.1f} MB"
        else:
            return f"{estimated / (1024 * 1024 * 1024):.1f} GB"