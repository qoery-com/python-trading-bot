"""
RSI Mean Reversion Strategy.
Based on J. Welles Wilder's Relative Strength Index (1978).

Rules:
- BUY when RSI crosses below lower_threshold (default 30) -> Oversold
- SELL when RSI crosses above upper_threshold (default 70) -> Overbought
"""

from decimal import Decimal

from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.message import Event
from nautilus_trader.indicators.rsi import RelativeStrengthIndex
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, PriceType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy


class RSIStrategyConfig(StrategyConfig, frozen=True):
    """Configuration for RSI Mean Reversion strategy."""
    
    instrument_id: str
    bar_type: str
    period: int = 14
    upper_threshold: int = 70
    lower_threshold: int = 30
    trade_size: float = 1.0


class RSIStrategy(Strategy):
    """
    RSI Mean Reversion Strategy.
    """
    
    def __init__(self, config: RSIStrategyConfig):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        
        # Register indicator
        self.rsi = RelativeStrengthIndex(config.period)

    def on_start(self):
        """Register instrument and bars."""
        self.register_indicator_for_bars(self.bar_type, self.rsi)
        
        # Subscribe to bars
        self.subscribe_bars(self.bar_type)

    def on_bar(self, bar: Bar):
        """Handle new bar data."""
        if not self.rsi.initialized:
            return

        # Get current RSI value
        rsi_value = self.rsi.value

        # TRADING LOGIC
        # -----------------------------------------------------------
        
        # BUY SIGNAL: RSI < Lower Threshold (Oversold)
        if rsi_value < self.config.lower_threshold:
            if self.portfolio.is_flat(self.instrument_id):
                self.log.info(f"RSI {rsi_value:.2f} < {self.config.lower_threshold} (Oversold) -> BUY")
                # Use cache to get instrument for precision
                instrument = self.cache.instrument(self.instrument_id)
                order = self.order_factory.market(
                    instrument_id=self.instrument_id,
                    order_side=OrderSide.BUY,
                    quantity=instrument.make_qty(self.config.trade_size),
                )
                self.submit_order(order)

        # SELL SIGNAL: RSI > Upper Threshold (Overbought)
        elif rsi_value > self.config.upper_threshold:
            if self.portfolio.is_net_long(self.instrument_id):
                self.log.info(f"RSI {rsi_value:.2f} > {self.config.upper_threshold} (Overbought) -> CLOSE LONG")
                self.close_position(self.instrument_id)

    def on_event(self, event: Event):
        pass

    def on_stop(self):
        self.cancel_all_orders(self.instrument_id)
        self.close_all_positions(self.instrument_id)
