"""
Integration Tests
Runs a full end-to-end backtest with synthetic data to verify 
that Data, Strings, and Engine all connect and generate trades.
"""

import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money, Currency
from nautilus_trader.model.data import BarType
from nautilus_trader.persistence.wranglers import BarDataWrangler

from strategies.sma import SMAStrategy, SMAStrategyConfig
from core.data_feed import get_instrument

def create_sine_wave_bars(instrument, length=200):
    """
    Create synthetic bars that form a sine wave to guarantee crossovers.
    """
    import math
    
    start_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
    data = []
    
    for i in range(length):
        # Generate sine wave price: 100 + 10 * sin(i / 10)
        # This guarantees price moves up and down
        price = 100 + 10 * math.sin(i / 10.0)
        
        # Determine OHLC
        # Add some noise/spread
        ts = start_time + timedelta(minutes=15 * i)
        
        data.append({
            "timestamp": ts,
            "open": price,
            "high": price + 0.5,
            "low": price - 0.5,
            "close": price,
            "volume": 1000.0,
        })
        
    df = pd.DataFrame(data)
    df = df.set_index("timestamp")
    
    # Create Bar objects using Wrangler
    bar_type = BarType.from_str(f"{instrument.id}-15-MINUTE-LAST-EXTERNAL")
    wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
    bars = wrangler.process(df)
    
    return bars, bar_type


def test_sma_integration_generates_trades():
    """
    Verify that SMA Strategy runs end-to-end and generates orders 
    on synthetic sine-wave data.
    """
    # 1. Setup Instrument & Data
    instrument = get_instrument("WETH-USDC")
    bars, bar_type = create_sine_wave_bars(instrument, length=200)
    
    # 2. Configure Engine
    venue_id = "BINANCE"
    venue = Venue(venue_id)
    
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="ERROR"), # Quiet logs
    )
    engine = BacktestEngine(config=config)
    
    # Define USDT since we are trading ETHUSDT
    USDT = Currency.from_str("USDT")
    
    # 3. Add Venue & Account
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT, # Use USDT to avoid conversion rate issues
        starting_balances=[Money(100_000, USDT)],
    )
    
    # 4. Add Instrument & Data
    engine.add_instrument(instrument)
    engine.add_data(bars)
    
    # 5. Configure Strategy (Fast period=10, Slow=20)
    # Sine wave period is roughly 2*PI*10 ~= 60 bars
    # SMA 10 and 20 should cross multiple times
    strat_config = SMAStrategyConfig(
        instrument_id=str(instrument.id),
        bar_type=str(bar_type),
        fast_period=10,
        slow_period=20,
        trade_size=1.0,
    )
    strategy = SMAStrategy(config=strat_config)
    engine.add_strategy(strategy)
    
    # 6. Run
    engine.run()
    
    # 7. Assertions
    orders = engine.trader.generate_order_fills_report()
    positions = engine.trader.generate_positions_report()
    
    # We expect at least a few trades from the sine wave crossovers
    assert len(orders) > 0, f"Strategy failed to generate orders. Orders: {len(orders)}"
    assert len(positions) > 0, f"Strategy failed to generate positions. Positions: {len(positions)}"
    
    # Simple success check is enough for integration
    print(f"Generated {len(orders)} orders and {len(positions)} positions.")
