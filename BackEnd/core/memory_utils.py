"""Memory management utilities for handling large datasets.

Provides chunked processing, memory-efficient operations, and graceful
degradation when memory is constrained.
"""

import gc
import logging
from typing import Optional, Callable, Any, List, Iterator
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Default chunk size for large DataFrames (rows)
DEFAULT_CHUNK_SIZE = 50000

# Maximum memory-efficient size before chunking
MAX_EFFICIENT_ROWS = 100000


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Downcast numeric columns to reduce memory usage.
    
    Converts int64 -> int32/int16, float64 -> float32 where safe.
    """
    if df.empty:
        return df
    
    optimized = df.copy()
    
    for col in optimized.columns:
        col_type = optimized[col].dtype
        
        # Downcast integers
        if col_type == np.int64:
            optimized[col] = pd.to_numeric(optimized[col], downcast='integer')
        elif col_type == np.float64:
            optimized[col] = pd.to_numeric(optimized[col], downcast='float')
    
    return optimized


def chunk_dataframe(df: pd.DataFrame, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Iterator[pd.DataFrame]:
    """Yield DataFrame chunks for memory-efficient processing.
    
    Args:
        df: Input DataFrame
        chunk_size: Number of rows per chunk
        
    Yields:
        DataFrame chunks
    """
    if len(df) <= chunk_size:
        yield df
        return
    
    for start in range(0, len(df), chunk_size):
        end = min(start + chunk_size, len(df))
        yield df.iloc[start:end].copy()


def safe_groupby_transform(
    df: pd.DataFrame,
    group_key: str,
    transform_func: Callable,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    fallback_value: Any = None
) -> pd.Series:
    """Memory-safe groupby transform with chunked fallback.
    
    Args:
        df: Input DataFrame
        group_key: Column to group by
        transform_func: Function to apply (e.g., 'sum', 'count')
        chunk_size: Chunk size for large DataFrames
        fallback_value: Value to return on error
        
    Returns:
        Transformed Series or fallback_value on error
    """
    if df.empty or group_key not in df.columns:
        return pd.Series(fallback_value if fallback_value is not None else np.nan, index=df.index)
    
    try:
        # Try standard operation first for small DataFrames
        if len(df) <= MAX_EFFICIENT_ROWS:
            if transform_func == 'sum':
                return df.groupby(group_key).transform('sum')
            elif transform_func == 'count':
                return df.groupby(group_key).transform('count')
            elif transform_func == 'cumcount':
                return df.groupby(group_key).cumcount()
            else:
                return df.groupby(group_key).transform(transform_func)
        
        # Chunked processing for large DataFrames
        logger.info(f"Using chunked groupby for {len(df):,} rows")
        results = []
        
        # Get unique groups
        unique_groups = df[group_key].unique()
        
        # Process each group separately to avoid large intermediate arrays
        for group_val in unique_groups:
            mask = df[group_key] == group_val
            group_df = df[mask]
            
            if transform_func == 'sum':
                result = group_df.sum()
            elif transform_func == 'count':
                result = len(group_df)
            elif transform_func == 'cumcount':
                result = pd.Series(range(len(group_df)), index=group_df.index)
            else:
                result = getattr(group_df, transform_func)()
            
            results.append((group_val, result))
            
            # Force garbage collection every 1000 groups
            if len(results) % 1000 == 0:
                gc.collect()
        
        # Combine results
        return pd.Series([r[1] for r in results], index=df.index)
        
    except MemoryError as e:
        logger.error(f"Memory error in groupby transform: {e}")
        gc.collect()
        return pd.Series(fallback_value if fallback_value is not None else np.nan, index=df.index)
    except Exception as e:
        logger.error(f"Error in groupby transform: {e}")
        return pd.Series(fallback_value if fallback_value is not None else np.nan, index=df.index)


def safe_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: Optional[str] = None,
    how: str = 'inner',
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> pd.DataFrame:
    """Memory-safe merge with chunked processing for large DataFrames.
    
    Args:
        left: Left DataFrame
        right: Right DataFrame  
        on: Key column(s) to merge on
        how: Merge type ('inner', 'left', 'right', 'outer')
        chunk_size: Chunk size for processing
        
    Returns:
        Merged DataFrame
    """
    if left.empty:
        return left
    if right.empty:
        return left if how in ['left', 'inner'] else right
    
    # For small DataFrames, use standard merge
    if len(left) <= chunk_size and len(right) <= chunk_size:
        try:
            return pd.merge(left, right, on=on, how=how)
        except MemoryError:
            logger.warning("Memory error on small merge, attempting chunked")
            gc.collect()
    
    # Chunked merge for large DataFrames
    logger.info(f"Using chunked merge: left={len(left):,}, right={len(right):,}")
    
    results = []
    
    for chunk in chunk_dataframe(left, chunk_size):
        try:
            merged = pd.merge(chunk, right, on=on, how=how)
            results.append(merged)
        except MemoryError as e:
            logger.error(f"Memory error merging chunk: {e}")
            gc.collect()
            # Return partial results
            if results:
                break
            else:
                return left  # Return original on complete failure
    
    if not results:
        return left
    
    try:
        return pd.concat(results, ignore_index=True)
    except MemoryError:
        logger.error("Memory error concatenating merge results")
        gc.collect()
        return results[0] if results else left


def cleanup_memory():
    """Force garbage collection and log memory status."""
    gc.collect()
    logger.debug("Memory cleanup performed")


class MemoryEfficientProcessor:
    """Context manager for memory-efficient DataFrame processing.
    
    Usage:
        with MemoryEfficientProcessor(df, chunk_size=10000) as proc:
            for chunk in proc.chunks():
                # Process chunk
                result = chunk.groupby('col').sum()
                proc.add_result(result)
        final_result = proc.combine_results()
    """
    
    def __init__(self, df: pd.DataFrame, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.df = df
        self.chunk_size = chunk_size
        self.results: List[pd.DataFrame] = []
        self._chunk_iter = None
    
    def __enter__(self):
        self._chunk_iter = chunk_dataframe(self.df, self.chunk_size)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup_memory()
        return False
    
    def chunks(self) -> Iterator[pd.DataFrame]:
        """Yield DataFrame chunks."""
        yield from self._chunk_iter
    
    def add_result(self, result: pd.DataFrame):
        """Add a processed chunk result."""
        self.results.append(result)
        # Cleanup every 10 chunks to prevent memory buildup
        if len(self.results) % 10 == 0:
            cleanup_memory()
    
    def combine_results(self) -> pd.DataFrame:
        """Combine all chunk results into single DataFrame."""
        if not self.results:
            return pd.DataFrame()
        
        try:
            return pd.concat(self.results, ignore_index=True)
        except MemoryError:
            logger.error("Memory error combining results, returning first chunk only")
            return self.results[0] if self.results else pd.DataFrame()


def safe_operation(func: Callable, *args, fallback_result: Any = None, **kwargs) -> Any:
    """Wrap any operation with memory error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        fallback_result: Value to return on error
        **kwargs: Keyword arguments
        
    Returns:
        Function result or fallback_result on error
    """
    try:
        return func(*args, **kwargs)
    except MemoryError as e:
        logger.error(f"Memory error in {func.__name__}: {e}")
        gc.collect()
        return fallback_result
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return fallback_result
