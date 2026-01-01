# python-trading-bot [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Just%20found%20this%20Open%20Source%20Crypto%20Trading%20Library%20(Arb%2C%20Sniper%2C%20Grid).%20Powered%20by%20Qoery.&url=https://github.com/qoery-com/python-trading-bot&hashtags=python,crypto,algotrading,passiveincome)

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![GitHub forks](https://img.shields.io/github/forks/qoery-com/python-trading-bot?style=social)
![GitHub stars](https://img.shields.io/github/stars/qoery-com/python-trading-bot?style=social)

> **Powered by [qoery-py](https://github.com/qoery-com/qoery-py) and [Nautilus Trader](https://github.com/nautechsystems/nautilus_trader)**

## Python Crypto Trading Bot
This repository hosts a collection of trading strategies (Arbitrage, Snipping, Grid) optimized for EVM chains (Ethereum, Base, Arbitrum, Polygon).

### Featured Strategies
All strategies are located in the `/strategies` folder.

| Strategy | Description | Status |
| :--- | :--- | :--- |
| **SMA Crossover** | Simple Moving Average (Golden/Death Cross). | ✅ Ready |
| **RSI Reversion** | Mean reversion based on RSI oscillator (Buy < 30, Sell > 70). | ✅ Ready |
| **Grid Trading** | Place buy/sell orders at fixed intervals. | 🚧 Planned |
| **Arbitrage** | Exploit price differences between DEXs. | 🚧 Planned |

---

## Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/qoery-com/python-trading-bot.git
cd python-trading-bot
pip install -r requirements.txt
```

### 2. Configure
First, **[sign up at Qoery.com](https://qoery.com)** to get your free API Key.

Then, copy the example environment file:
```bash
cp .env.example .env
```
Edit `.env` and paste your key:
```text
QOERY_API_KEY=your_api_key_here
```

### 3. Run a Backtest
Run a simulation using historical data from Qoery.

**SMA Strategy:**
```bash
python main.py backtest --strategy sma --symbol WETH-USDC --interval 15m --days 30
```

**RSI Strategy:**
```bash
python main.py backtest --strategy rsi --symbol WETH-USDC --interval 1h --days 14
```

### 4. Custom Parameters
You can pass custom parameters to strategies using the `--params` flag.
```bash
python main.py backtest --strategy sma --symbol WETH-USDC --params fast_period=20,slow_period=50
```

### 5. Live Trading (Paper Mode)
Currently in Beta (Paper Trading only).
```bash
python main.py live --strategy sma --symbol WETH-USDC
```

## Contributing
We welcome contributions! Whether it's a new strategy, a bug fix, or a documentation improvement.
**We offer rewards (Free Qoery Plan)** for significant contributions.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
