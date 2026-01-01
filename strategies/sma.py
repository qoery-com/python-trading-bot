"""
SMA Crossover Strategy for Nautilus Trader.
Generates BUY signals when fast SMA crosses above slow SMA.
Generates SELL signals when fast SMA crosses below slow SMA.
"""

from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.message import Event
from nautilus_trader.indicators.average.sma import SimpleMovingAverage
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy


class SMAStrategyConfig(StrategyConfig, frozen=True):
    """Configuration for SMA crossover strategy."""
    
    instrument_id: str
    bar_type: str
    fast_period: int = 10
    slow_period: int = 20
    trade_size: float = 1.0


class SMAStrategy(Strategy):
    """
    Simple Moving Average crossover strategy.
    
    Entry: Buy when fast SMA crosses above slow SMA
    Exit: Sell when fast SMA crosses below slow SMA
    """
    
    def __init__(self, config: SMAStrategyConfig):
        super().__init__(config)
        
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.trade_size = config.trade_size
        
        # Create indicators
        self.fast_sma = SimpleMovingAverage(config.fast_period)
        self.slow_sma = SimpleMovingAverage(config.slow_period)
        
        # Track previous values for crossover detection
        self._prev_fast = None
        self._prev_slow = None
    
    def on_start(self) -> None:
        """Called when strategy starts."""
        self.log.info(f"Starting SMA strategy on {self.instrument_id}")
        
        # Register indicators to receive bar updates
        self.register_indicator_for_bars(self.bar_type, self.fast_sma)
        self.register_indicator_for_bars(self.bar_type, self.slow_sma)
        
        # Subscribe to bars
        self.subscribe_bars(self.bar_type)
    
    def on_bar(self, bar: Bar) -> None:
        """Called on each new bar."""
        # Wait for indicators to be ready
        if not self.fast_sma.initialized or not self.slow_sma.initialized:
            return
        
        fast_value = self.fast_sma.value
        slow_value = self.slow_sma.value
        
        # Check for crossover
        if self._prev_fast is not None and self._prev_slow is not None:
            # Bullish crossover: fast crosses above slow
            if self._prev_fast <= self._prev_slow and fast_value > slow_value:
                self._enter_long()
            
            # Bearish crossover: fast crosses below slow
            elif self._prev_fast >= self._prev_slow and fast_value < slow_value:
                self._exit_long()
        
        # Update previous values
        self._prev_fast = fast_value
        self._prev_slow = slow_value
    
    def _enter_long(self) -> None:
        """Enter a long position."""
        if self.portfolio.is_flat(self.instrument_id):
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.instrument.make_qty(self.trade_size),
            )
            self.submit_order(order)
            self.log.info(f"BUY signal - entering long at {self.fast_sma.value:.2f}/{self.slow_sma.value:.2f}")
    
    def _exit_long(self) -> None:
        """Exit long position."""
        if self.portfolio.is_net_long(self.instrument_id):
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=self.instrument.make_qty(self.trade_size),
            )
            self.submit_order(order)
            self.log.info(f"SELL signal - exiting long at {self.fast_sma.value:.2f}/{self.slow_sma.value:.2f}")
    
    @property
    def instrument(self) -> Instrument:
        """Get the trading instrument."""
        return self.cache.instrument(self.instrument_id)
    
    def on_stop(self) -> None:
        """Called when strategy stops."""
        self.log.info("SMA strategy stopped")
