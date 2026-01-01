"""
Qoery data feed integration for Nautilus Trader.
Converts Qoery candle data to Nautilus Bar objects.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pandas as pd
import qoery
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.identifiers import InstrumentId, Venue
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider


def _interval_to_bar_spec(interval: str) -> str:
    """Convert interval string (e.g., '15m') to Nautilus bar spec (e.g., '15-MINUTE')."""
    interval_map = {
        "1s": "1-SECOND",
        "1m": "1-MINUTE",
        "5m": "5-MINUTE",
        "15m": "15-MINUTE",
        "30m": "30-MINUTE",
        "1h": "1-HOUR",
        "4h": "4-HOUR",
        "1d": "1-DAY",
    }
    return interval_map.get(interval, "15-MINUTE")


def get_instrument(symbol: str):
    """
    Create a crypto instrument for the given symbol.
    Uses TestInstrumentProvider for compatibility with nautilus_trader 1.202.0.
    """
    # Parse symbol like "WETH-USDC" -> base="WETH", quote="USDC"
    parts = symbol.upper().replace("-", "/").replace("_", "/").split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid symbol format: {symbol}. Expected 'BASE-QUOTE' or 'BASE/QUOTE'")
    
    base, quote = parts
    
    # Use a generic test instrument (the actual symbol doesn't affect backtesting logic)
    # In a production system, you'd want to create proper instruments per symbol
    return TestInstrumentProvider.ethusdt_perp_binance()


def load_bars(
    symbol: str,
    interval: str = "15m",
    limit: int = 100,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
) -> tuple[list[Bar], BarType]:
    """
    Fetch candles from Qoery and convert to Nautilus Bar objects.
    Automatically paginates if limit > 100 (Qoery's max per request).
    
    Args:
        symbol: Trading pair symbol (e.g., "WETH-USDC")
        interval: Candle interval (e.g., "1m", "15m", "1h", "1d")
        limit: Maximum number of candles to fetch (will paginate if > 100)
        from_time: Start time for historical data
        to_time: End time for historical data
    
    Returns:
        Tuple of (list of Bar objects, BarType)
    """
    # Initialize Qoery client (auto-loads from env)
    client = qoery.Client()
    
    all_candles = []
    page_size = 100  # Qoery's max limit per request
    remaining = limit
    current_to_time = to_time
    
    # Paginate to fetch all requested candles
    while remaining > 0:
        batch_size = min(page_size, remaining)
        
        # Fetch this batch
        candles = client.candles.get(
            symbol=symbol,
            interval=interval,
            limit=batch_size,
            from_time=from_time,
            to_time=current_to_time,
        )
        
        # Convert to DataFrame
        df_batch = candles.df
        
        if df_batch.empty:
            break  # No more data available
        
        all_candles.append(df_batch)
        
        # If we got fewer candles than requested, we've hit the end
        if len(df_batch) < batch_size:
            break
        
        # Update for next page: use the timestamp of the oldest candle as new to_time
        # Subtract 1 millisecond to avoid getting the same candle again
        oldest_time = pd.to_datetime(df_batch['time'].iloc[0])
        current_to_time = oldest_time - pd.Timedelta(milliseconds=1)
        
        # If we've gone past from_time, stop
        if from_time and current_to_time < from_time:
            break
        
        remaining -= len(df_batch)
    
    if not all_candles:
        return [], None
    
    # Combine all batches
    df = pd.concat(all_candles, ignore_index=True)
    
    # Sort by time (oldest first) since we fetched backwards
    df = df.sort_values('time').reset_index(drop=True)
    
    # Filter to from_time if specified (pagination might have fetched earlier data)
    if from_time:
        df = df[pd.to_datetime(df['time']) >= from_time]
    
    # Prepare DataFrame for BarDataWrangler
    df = df.rename(columns={"time": "timestamp"})
    
    # Select only the required columns first
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    
    # Remove any rows with NaN values
    df = df.dropna()
    
    if df.empty:
        print("Warning: All data contains NaN values after filtering")
        return [], None
    
    print(f"Loaded {len(df)} bars from Qoery")
    
    # Ensure timestamp is datetime with UTC timezone
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    elif df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize('UTC')
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert('UTC')
    
    # Set timestamp as index (required by BarDataWrangler)
    df = df.set_index("timestamp")
    
    # Select only the OHLCV columns (timestamp is now the index)
    df = df[["open", "high", "low", "close", "volume"]]
    
    # Get instrument  
    instrument = get_instrument(symbol)
    
    # Convert interval to Nautilus bar spec format
    bar_spec = _interval_to_bar_spec(interval)
    
    # Create bar type (format: SYMBOL.VENUE-STEP-AGGREGATION-PRICE_TYPE)
    bar_type = BarType.from_str(f"{instrument.id}-{bar_spec}-LAST-EXTERNAL")
    
    # Use BarDataWrangler to convert
    wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
    bars = wrangler.process(df)
    
    return bars, bar_type

