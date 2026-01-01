"""
Strategy Registry
Helper functions to dynamically discover and load strategies.
"""

import importlib
import inspect
import pkgutil
from typing import Type, Tuple, Dict, Optional

from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig

# Type alias for the strategy pair
StrategyPair = Tuple[Type[Strategy], Type[StrategyConfig]]


class StrategyRegistry:
    """
    Registry to dynamically load strategies from the strategies/ directory.
    """
    
    @staticmethod
    def load_strategy(name: str) -> StrategyPair:
        """
        Load a strategy and its config by name (e.g., 'sma').
        
        Args:
            name: The name of the strategy module (file name without .py)
            
        Returns:
            Tuple containing (StrategyClass, StrategyConfigClass)
            
        Raises:
            ValueError: If strategy not found or invalid
        """
        try:
            # Dynamically import the module
            module_name = f"strategies.{name}"
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise ValueError(f"Strategy '{name}' not found. Ensure 'strategies/{name}.py' exists.") from e
            
        strategy_class = None
        config_class = None
        
        # Inspect module members
        for _, member in inspect.getmembers(module):
            if inspect.isclass(member):
                # Find the Strategy subclass (excluding the base Strategy class itself)
                if issubclass(member, Strategy) and member is not Strategy:
                    strategy_class = member
                
                # Find the StrategyConfig subclass (excluding the base StrategyConfig class itself)
                if issubclass(member, StrategyConfig) and member is not StrategyConfig:
                    config_class = member
        
        if not strategy_class:
            raise ValueError(f"No Strategy class found in {module_name}")
            
        if not config_class:
            # Fallback: if no specific config found, check if the strategy has a config_class attribute?
            # Or just warn? For Nautilus, a config is usually required.
            raise ValueError(f"No StrategyConfig class found in {module_name}")
            
        return strategy_class, config_class

    @staticmethod
    def available_strategies() -> Dict[str, str]:
        """
        Scan the strategies directory and return available strategies.
        
        Returns:
            Dict mapping strategy_name -> description (docstring)
        """
        available = {}
        import strategies
        
        # Scan the 'strategies' package directory
        for _, name, is_pkg in pkgutil.iter_modules(strategies.__path__):
            if is_pkg:
                continue
                
            try:
                module = importlib.import_module(f"strategies.{name}")
                # Try to find the docstring of the module or the strategy class
                description = module.__doc__ or ""
                
                # Refine description from class if possible
                for _, member in inspect.getmembers(module):
                    if inspect.isclass(member) and issubclass(member, Strategy) and member is not Strategy:
                        if member.__doc__:
                            description = member.__doc__
                        break
                        
                available[name] = description.strip().split('\n')[0] if description else "No description"
            except ImportError:
                continue
                
        return available
