"""
Tests for Core Components using Pytest
"""

import pytest
import pandas as pd
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig

from core.registry import StrategyRegistry
from core.data_feed import get_instrument, _interval_to_bar_spec
from main import parse_params


class TestDataFeedLoading:
    """Test data loading logic with mocked Qoery client."""
    
    @patch('core.data_feed.qoery.Client')
    def test_load_bars_pagination(self, mock_client_cls):
        """Test that load_bars correctly paginates and combines data."""
        from core.data_feed import load_bars
        
        # Setup mock responses
        mock_instance = mock_client_cls.return_value
        
        # Create two batches of fake data to simulate pagination
        # Page size in code is 100.
        # We want to fetch 150 total.
        # Batch 1: 100 items (Newest)
        # Batch 2: 50 items (Oldest)
        
        base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Batch 1: Times 50..149 (100 items)
        times1 = [base_time + pd.Timedelta(minutes=i) for i in range(50, 150)]
        df1 = pd.DataFrame({
            'time': times1,
            'open': [100.0] * 100, 'high': [105.0] * 100, 'low': [95.0] * 100, 'close': [101.0] * 100, 'volume': [1000] * 100
        })
        
        # Batch 2: Times 0..49 (50 items)
        times2 = [base_time + pd.Timedelta(minutes=i) for i in range(0, 50)]
        df2 = pd.DataFrame({
            'time': times2,
            'open': [100.0] * 50, 'high': [105.0] * 50, 'low': [95.0] * 50, 'close': [101.0] * 50, 'volume': [1000] * 50
        })
        
        # Mock .candles.get() to return these in sequence
        # Note: load_bars fetches "newest" first if just using to_time, but here the loop logic
        # is determined by the implementation.
        # Implementation:
        # 1. Fetch batch_size (100) -> returns df1
        # 2. Update to_time = df1.oldest - 1ms
        # 3. Fetch batch_size (50) -> returns df2
        mock_instance.candles.get.side_effect = [
            MagicMock(df=df1),
            MagicMock(df=df2),
            MagicMock(df=pd.DataFrame()) 
        ]
        
        # Run load_bars requesting 150 bars
        bars, bar_type = load_bars("ETH-USDC", limit=150)
        
        # Assertions
        assert len(bars) == 150 # Should have combined both batches (100+50)
        assert mock_instance.candles.get.call_count >= 2
        
        # Verify first bar is the oldest (Index 0 of combined sorted df)
        assert bars[0].ts_event == df2.iloc[0]['time'].timestamp() * 1e9 # ns
        # Verify last bar is newest
        assert bars[-1].ts_event == df1.iloc[-1]['time'].timestamp() * 1e9

    @patch('core.data_feed.qoery.Client')
    def test_load_bars_nan_filtering(self, mock_client_cls):
        """Test that rows with NaN values are dropped."""
        from core.data_feed import load_bars
        
        mock_instance = mock_client_cls.return_value
        
        # Create data with some NaNs
        df = pd.DataFrame({
            'time': [datetime(2025, 1, 1, 10, i, tzinfo=timezone.utc) for i in range(5)],
            'open': [100.0, None, 100.0, 100.0, 100.0], # One NaN
            'high': [105.0] * 5, 'low': [95.0] * 5, 'close': [101.0] * 5, 'volume': [1000] * 5
        })
        
        mock_instance.candles.get.return_value = MagicMock(df=df)
        
        bars, _ = load_bars("ETH-USDC", limit=10)
        
        # Should have dropped the 2nd row (index 1)
        assert len(bars) == 4


def test_get_instrument_edge_cases():
    """Test instrument creation edge cases."""
    
    # Test valid messy input
    inst = get_instrument("weth_usdc") # Lowercase with underscore
    assert str(inst.base_currency) == "ETH" 
    
    # Test invalid format
    with pytest.raises(ValueError):
        get_instrument("INVALIDFORMAT") # No separator


def test_available_strategies():
    """Test that we can list strategies."""
    available = StrategyRegistry.available_strategies()
    assert isinstance(available, dict)
    assert "sma" in available
    assert "rsi" in available
    assert isinstance(available["sma"], str)


def test_load_strategy_sma():
    """Test loading the SMA strategy."""
    StrategyClass, ConfigClass = StrategyRegistry.load_strategy("sma")
    
    assert issubclass(StrategyClass, Strategy)
    assert issubclass(ConfigClass, StrategyConfig)
    assert StrategyClass.__name__ == "SMAStrategy"
    assert ConfigClass.__name__ == "SMAStrategyConfig"


def test_load_strategy_invalid():
    """Test loading a non-existent strategy."""
    with pytest.raises(ValueError):
        StrategyRegistry.load_strategy("non_existent_strategy_123")


def test_interval_to_bar_spec():
    """Test conversion of interval strings to Nautilus bar specs."""
    assert _interval_to_bar_spec("15m") == "15-MINUTE"
    assert _interval_to_bar_spec("1h") == "1-HOUR"
    assert _interval_to_bar_spec("1d") == "1-DAY"
    
    # Test fallback - defaults to 15-MINUTE if unknown
    assert _interval_to_bar_spec("33x") == "15-MINUTE"


def test_get_instrument():
    """Test instrument creation."""
    symbol = "WETH-USDC"
    instrument = get_instrument(symbol)
    
    # Check ID string representation match
    # Note: Currently returns hardcoded ETHUSDT-PERP.BINANCE due to TestInstrumentProvider usage
    assert str(instrument.id) == "ETHUSDT-PERP.BINANCE"
    assert str(instrument.base_currency) == "ETH"
    assert str(instrument.quote_currency) == "USDT"


def test_parse_params():
    """Test parsing of CLI params string."""
    # Test empty
    assert parse_params("") == {}
    assert parse_params(None) == {}
    
    # Test ints
    assert parse_params("a=1,b=2") == {"a": 1, "b": 2}
    
    # Test floats
    assert parse_params("x=1.5,y=0.001") == {"x": 1.5, "y": 0.001}
    
    # Test mixed
    assert parse_params("fast=10,ratio=0.5,name=custom") == {"fast": 10, "ratio": 0.5, "name": "custom"}
    
    # Test whitespace
    assert parse_params(" fast = 10 , slow = 20 ") == {"fast": 10, "slow": 20}
