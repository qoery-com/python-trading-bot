# Contributing to Python Crypto Trading Bot

First off, thank you for considering contributing to this project! It's people like you that make the open-source community such an amazing place to learn, inspire, and create.

**High Impact Opportunity**: This repository is designed to demonstrate the power of the [qoery.com](https://qoery.com/) API. 

## Rewards for Contributors

We want to reward high-quality contributions. **If you provide a new strategy, fix functionality bugs, or significantly improve the codebase, you will receive ONE MONTH FREE of the Basic Plan from [qoery.com](https://qoery.com/).**

To claim your reward after your Pull Request is merged, please reach out to us (contact details will be provided upon merge) or open an issue referencing your merged PR.

## Project Goal

The primary goal of this repository is to provide the highest quality repo of strategies you can backtest and/or trade live at any time.

We welcome contributions that align with these goals, especially those that add new, profitable, or interesting strategies using the API.

## How to Contribute

### 1. Fork and Clone
Fork the repository to your own GitHub account and then clone it to your local machine:
```bash
git clone https://github.com/YOUR_USERNAME/python-crypto-trading-bot.git
cd python-crypto-trading-bot
```

### 2. Set Up Your Environment
Ensure you have the necessary dependencies installed. We recommend using a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You will need a Qoery API key to run strategies. Sign up at [qoery.com](https://qoery.com/) and create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env and add your QOERY_API_KEY
```

### 3. Create a Branch
Create a new branch for your feature or bug fix:
```bash
git checkout -b feature/my-new-strategy
```

### 4. Make Your Changes
- **Strategies**: If adding a new strategy, place it in the `strategies/` directory. Ensure it follows the `BaseStrategy` interface.
- **Code Style**: Please keep the code clean and readable.
- **Tests**: Add unit tests in the `tests/` directory to verify your changes. Run existing tests to ensure no regressions:
  ```bash
  pytest
  ```

### 5. Push and Open a Pull Request
Push your changes to your fork and submit a Pull Request to the `main` branch of this repository.

```bash
git push origin feature/my-new-strategy
```

In your Pull Request description, please explain:
- What changes you made.
- Why you made them.
- (If applicable) Results of backtesting your new strategy.

## Pull Request Guidelines

- Ensure your code runs without errors.
- Update `requirements.txt` if you added new dependencies.
- If you added a strategy, please include a brief description of how it works in the docstring or PR description.

Thank you for contributing!
