"""
Trading Bot CLI - Backtest and Live Trading with Nautilus Trader + Qoery
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider

from core.data_feed import load_bars, get_instrument
from core.registry import StrategyRegistry


def parse_params(params_str: str) -> dict:
    """Parse key=value,key=value string into dict."""
    if not params_str:
        return {}
    
    params = {}
    for pair in params_str.split(','):
        if '=' not in pair:
            continue
        key, value = pair.split('=', 1)
        # Try to parse as int/float, otherwise keep as string
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
        params[key.strip()] = value
    return params


def run_backtest(
    strategy: str,
    symbol: str,
    interval: str = "15m",
    days: int = 30,
    capital: float = 100000,
    size: float = 1.0,
    venue: str = "BINANCE",
    params: dict = None,
    output: str = None,
    verbose: bool = False,
) -> None:
    """Run a backtest with the specified strategy and parameters."""
    
    if params is None:
        params = {}
    
    # Load strategy class dynamically
    try:
        StrategyClass, ConfigClass = StrategyRegistry.load_strategy(strategy)
    except ValueError as e:
        print(f"Error: {e}")
        return

    print(f"\n{'='*60}")
    print(f"Running Backtest")
    print(f"{'='*60}")
    print(f"Strategy: {strategy} ({StrategyClass.__name__})")
    print(f"Symbol: {symbol}")
    print(f"Interval: {interval}")
    print(f"Days: {days}")
    print(f"Capital: ${capital:,.2f}")
    print(f"Trade Size: {size}")
    print(f"Venue: {venue}")
    if params:
        print(f"Params: {params}")
    print(f"{'='*60}\n")
    
    # Load data from Qoery
    print("Loading data from Qoery...")
    to_time = datetime.now(timezone.utc)
    from_time = to_time - timedelta(days=days)
    
    # Calculate how many bars we need
    # 15m interval = 4 bars/hour = 96 bars/day
    interval_map = {
        "1m": 1440,    # bars per day
        "5m": 288,
        "15m": 96,
        "30m": 48,
        "1h": 24,
        "4h": 6,
        "1d": 1,
    }
    bars_per_day = interval_map.get(interval, 96)  # default to 15m
    requested_bars = days * bars_per_day
    
    bars, bar_type = load_bars(
        symbol=symbol,
        interval=interval,
        from_time=from_time,
        to_time=to_time,
        limit=requested_bars,
    )
    
    if not bars:
        print("Error: No data returned from Qoery")
        return
    
    print(f"Loaded {len(bars)} bars from {bars[0].ts_event} to {bars[-1].ts_event}")
    
    # Get instrument
    instrument = get_instrument(symbol)
    venue_obj = Venue(venue)
    
    # Configure backtest engine
    log_level = "DEBUG" if verbose else "INFO"
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level=log_level),
    )
    
    engine = BacktestEngine(config=config)
    
    # Add a trading venue
    engine.add_venue(
        venue=venue_obj,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(capital, USD)],
    )
    
    # Add instrument and data
    engine.add_instrument(instrument)
    engine.add_data(bars)
    
    # Initialize strategy
    # Merge default params with user-provided params
    strategy_params = {
        'instrument_id': str(bars[0].bar_type.instrument_id),
        'bar_type': str(bar_type),
        'trade_size': size,
        **params  # Override with user params
    }
    
    try:
        strategy_config = ConfigClass(**strategy_params)
        strategy_instance = StrategyClass(config=strategy_config)
        engine.add_strategy(strategy_instance)
    except Exception as e:
        print(f"Error: Failed to initialize {StrategyClass.__name__}: {e}")
        return
    
    # Run the backtest
    engine.run()
    
    # Print results
    print(f"\n{'='*60}")
    print("Backtest Results")
    print(f"{'='*60}")
    print(f"Total Orders: {len(engine.trader.generate_order_fills_report())}")
    print(f"Total Positions: {len(engine.trader.generate_positions_report())}")
    print(f"\n(See detailed performance metrics in the logs above)")
    print(f"{'='*60}\n")
    
    # Save results if output specified
    if output:
        results = {
            'strategy': strategy,
            'symbol': symbol,
            'interval': interval,
            'days': days,
            'capital': capital,
            'size': size,
            'venue': venue,
            'params': params,
            'orders': len(engine.trader.generate_order_fills_report()),
            'positions': len(engine.trader.generate_positions_report()),
        }
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {output}\n")
    
    # Dispose
    engine.dispose()
    print("Backtest complete!")


def run_live(
    strategy: str,
    symbol: str,
    interval: str = "15m",
) -> None:
    """
    Run live trading (not yet implemented).
    """
    print(f"\n{'='*60}")
    print(f"Live Trading (Paper Mode)")
    print(f"{'='*60}")
    print(f"Strategy: {strategy}")
    print(f"Symbol: {symbol}")
    print(f"Interval: {interval}")
    print(f"{'='*60}\n")
    
    print("⚠️  Live trading is currently unavailable.")
    print("   Qoery.com REST API is supported, but WebSockets are required")
    print("   for reliable live trading event loops.")
    print("\n   Streaming support is on the Qoery roadmap for Early 2026.")
    print("   Until then, please use 'backtest' mode to validate strategies.")


def list_strategies() -> None:
    """List available strategies."""
    print("\nAvailable Strategies:")
    print("-" * 60)
    print(f"{'Name':<15} | {'Description'}")
    print("-" * 60)
    
    strategies = StrategyRegistry.available_strategies()
    
    if not strategies:
        print("No strategies found in strategies/ directory.")
    
    for name, desc in strategies.items():
        print(f"  {name:<13} | {desc}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Trading Bot CLI - Backtest and Live Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available strategies")
    
    # Backtest command
    backtest_parser = subparsers.add_parser("backtest", help="Run a backtest")
    backtest_parser.add_argument("--strategy", "-s", default="sma", help="Strategy to use (default: sma)")
    backtest_parser.add_argument("--symbol", required=True, help="Trading pair (e.g., WETH-USDC)")
    backtest_parser.add_argument("--interval", "-i", default="15m", help="Candle interval (default: 15m)")
    backtest_parser.add_argument("--days", "-d", type=int, default=30, help="Days of history (default: 30)")
    backtest_parser.add_argument("--capital", "-c", type=float, default=100000, help="Initial capital (default: 100000)")
    backtest_parser.add_argument("--size", type=float, default=1.0, help="Trade size (default: 1.0)")
    backtest_parser.add_argument("--venue", default="BINANCE", help="Trading venue (default: BINANCE)")
    backtest_parser.add_argument("--params", "-p", default="", help="Strategy params as key=value,key=value (e.g., fast_period=10,slow_period=20)")
    backtest_parser.add_argument("--output", "-o", help="Save results to JSON file")
    backtest_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    # Live trading command
    live_parser = subparsers.add_parser("live", help="Run live trading (paper mode)")
    live_parser.add_argument("--strategy", "-s", default="sma", help="Strategy to use (default: sma)")
    live_parser.add_argument("--symbol", required=True, help="Trading pair (e.g., WETH-USDC)")
    live_parser.add_argument("--interval", "-i", default="15m", help="Candle interval (default: 15m)")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_strategies()
    elif args.command == "backtest":
        params_dict = parse_params(args.params)
        run_backtest(
            strategy=args.strategy,
            symbol=args.symbol,
            interval=args.interval,
            days=args.days,
            capital=args.capital,
            size=args.size,
            venue=args.venue,
            params=params_dict,
            output=args.output,
            verbose=args.verbose,
        )
    elif args.command == "live":
        run_live(
            strategy=args.strategy,
            symbol=args.symbol,
            interval=args.interval,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
