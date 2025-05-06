import asyncio
import time
from termcolor import colored
from datetime import datetime

from quotexpy.utils.operation_type import OperationType
from quotexpy.utils.candles_period import CandlesPeriod


class TradingStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, client, asset, amount=1, duration=60):
        self.client = client
        self.asset = asset
        self.amount = amount
        self.duration = duration
        self.wins = 0
        self.losses = 0
        self.total_profit = 0
        
    async def execute_trade(self, action):
        """Execute a trade with the given action"""
        status, trade_info = await self.client.trade(action, self.amount, self.asset, self.duration)
        
        if status:
            print(colored("[INFO]: ", "blue"), f"Trade executed. ID: {trade_info.get('id', 'Unknown')}")
            print(colored("[INFO]: ", "blue"), "Waiting for result...")
            
            if await self.client.check_win(trade_info.get('id')):
                profit = self.client.get_profit()
                self.wins += 1
                self.total_profit += profit
                print(colored("[INFO]: ", "green"), f"Win -> Profit: ${profit}")
                print(colored("[INFO]: ", "cyan"), f"Stats: W:{self.wins} L:{self.losses} Profit:${self.total_profit}")
                return True, profit
            else:
                loss = abs(self.client.get_profit())
                self.losses += 1
                self.total_profit -= loss
                print(colored("[INFO]: ", "red"), f"Loss -> Lost: ${loss}")
                print(colored("[INFO]: ", "cyan"), f"Stats: W:{self.wins} L:{self.losses} Profit:${self.total_profit}")
                return False, -loss
        else:
            print(colored("[ERROR]: ", "red"), "Trade execution failed")
            return False, 0
            
    async def check_asset_availability(self):
        """Check if the asset is available for trading"""
        asset_query = self.asset
        asset_open = self.client.check_asset(asset_query)
        
        if not asset_open or not asset_open[2]:
            print(colored("[WARN]: ", "yellow"), f"Asset {self.asset} is closed.")
            otc_asset = f"{self.asset}_otc"
            print(colored("[WARN]: ", "yellow"), f"Trying OTC Asset -> {otc_asset}")
            asset_query = otc_asset
            asset_open = self.client.check_asset(asset_query)
            
            if asset_open and asset_open[2]:
                self.asset = otc_asset
                return True
            else:
                print(colored("[ERROR]: ", "red"), f"No available version of {self.asset} found.")
                return False
        
        return True


class SimpleMovingAverageStrategy(TradingStrategy):
    """Trading strategy based on Simple Moving Average crossover"""
    
    def __init__(self, client, asset, amount=1, duration=60, short_period=5, long_period=20):
        super().__init__(client, asset, amount, duration)
        self.short_period = short_period  # Short MA period
        self.long_period = long_period    # Long MA period
        
    async def run(self, max_trades=5, interval=70):
        """Run the SMA strategy for a specified number of trades"""
        if not await self.check_asset_availability():
            return
            
        print(colored("[INFO]: ", "blue"), f"Starting SMA strategy on {self.asset}")
        print(colored("[INFO]: ", "blue"), f"Parameters: Short MA={self.short_period}, Long MA={self.long_period}")
        
        trades_executed = 0
        
        while trades_executed < max_trades:
            # Get candle data
            candles = await self.client.get_candle_v2(self.asset, CandlesPeriod.ONE_MINUTE)
            
            if not candles:
                print(colored("[ERROR]: ", "red"), "Failed to get candle data")
                await asyncio.sleep(5)
                continue
                
            # Extract close prices
            close_prices = [candle.get('close', 0) for candle in candles]
            
            # Calculate moving averages
            if len(close_prices) >= self.long_period:
                short_ma = sum(close_prices[-self.short_period:]) / self.short_period
                long_ma = sum(close_prices[-self.long_period:]) / self.long_period
                
                print(colored("[INFO]: ", "blue"), f"Short MA: {short_ma:.5f}, Long MA: {long_ma:.5f}")
                
                # Trading logic
                if short_ma > long_ma:
                    print(colored("[SIGNAL]: ", "green"), "CALL signal detected")
                    await self.execute_trade(OperationType.CALL)
                    trades_executed += 1
                elif short_ma < long_ma:
                    print(colored("[SIGNAL]: ", "red"), "PUT signal detected")
                    await self.execute_trade(OperationType.PUT)
                    trades_executed += 1
                else:
                    print(colored("[INFO]: ", "yellow"), "No clear signal detected")
            
            # Wait before next check
            print(colored("[INFO]: ", "blue"), f"Waiting {interval} seconds before next analysis...")
            await asyncio.sleep(interval)
            
        print(colored("[INFO]: ", "cyan"), "Strategy completed")
        print(colored("[SUMMARY]: ", "cyan"), f"Total trades: {self.wins + self.losses}")
        print(colored("[SUMMARY]: ", "cyan"), f"Wins: {self.wins}, Losses: {self.losses}")
        print(colored("[SUMMARY]: ", "cyan"), f"Win rate: {(self.wins / (self.wins + self.losses)) * 100:.2f}%")
        print(colored("[SUMMARY]: ", "cyan"), f"Total profit: ${self.total_profit}")


class RSIStrategy(TradingStrategy):
    """Trading strategy based on Relative Strength Index (RSI)"""
    
    def __init__(self, client, asset, amount=1, duration=60, rsi_period=14, oversold=30, overbought=70):
        super().__init__(client, asset, amount, duration)
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        
    def calculate_rsi(self, closes):
        """Calculate the Relative Strength Index"""
        if len(closes) < self.rsi_period + 1:
            return None
            
        # Get price changes
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        # Calculate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # Calculate average gains and losses
        avg_gain = sum(gains[-self.rsi_period:]) / self.rsi_period
        avg_loss = sum(losses[-self.rsi_period:]) / self.rsi_period
        
        if avg_loss == 0:
            return 100  # No losses means RSI = 100
            
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    async def run(self, max_trades=5, interval=70):
        """Run the RSI strategy for a specified number of trades"""
        if not await self.check_asset_availability():
            return
            
        print(colored("[INFO]: ", "blue"), f"Starting RSI strategy on {self.asset}")
        print(colored("[INFO]: ", "blue"), f"Parameters: RSI Period={self.rsi_period}, Oversold={self.oversold}, Overbought={self.overbought}")
        
        trades_executed = 0
        
        while trades_executed < max_trades:
            # Get candle data
            candles = await self.client.get_candle_v2(self.asset, CandlesPeriod.ONE_MINUTE)
            
            if not candles:
                print(colored("[ERROR]: ", "red"), "Failed to get candle data")
                await asyncio.sleep(5)
                continue
                
            # Extract close prices
            close_prices = [candle.get('close', 0) for candle in candles]
            
            # Calculate RSI
            rsi = self.calculate_rsi(close_prices)
            
            if rsi is not None:
                print(colored("[INFO]: ", "blue"), f"Current RSI: {rsi:.2f}")
                
                # Trading logic - buy when oversold, sell when overbought
                if rsi <= self.oversold:
                    print(colored("[SIGNAL]: ", "green"), f"Oversold (RSI={rsi:.2f}) - CALL signal")
                    await self.execute_trade(OperationType.CALL)
                    trades_executed += 1
                elif rsi >= self.overbought:
                    print(colored("[SIGNAL]: ", "red"), f"Overbought (RSI={rsi:.2f}) - PUT signal")
                    await self.execute_trade(OperationType.PUT)
                    trades_executed += 1
                else:
                    print(colored("[INFO]: ", "yellow"), f"No signal (RSI={rsi:.2f} is in neutral zone)")
            else:
                print(colored("[INFO]: ", "yellow"), "Not enough data to calculate RSI")
            
            # Wait before next check
            print(colored("[INFO]: ", "blue"), f"Waiting {interval} seconds before next analysis...")
            await asyncio.sleep(interval)
            
        print(colored("[INFO]: ", "cyan"), "Strategy completed")
        print(colored("[SUMMARY]: ", "cyan"), f"Total trades: {self.wins + self.losses}")
        print(colored("[SUMMARY]: ", "cyan"), f"Wins: {self.wins}, Losses: {self.losses}")
        print(colored("[SUMMARY]: ", "cyan"), f"Win rate: {(self.wins / max(1, self.wins + self.losses)) * 100:.2f}%")
        print(colored("[SUMMARY]: ", "cyan"), f"Total profit: ${self.total_profit}")


class MartingaleStrategy(TradingStrategy):
    """Martingale trading strategy - doubles bet after each loss"""
    
    def __init__(self, client, asset, base_amount=1, duration=60, max_step=4):
        super().__init__(client, asset, base_amount, duration)
        self.base_amount = base_amount  # Initial bet amount
        self.max_step = max_step  # Maximum number of steps (to limit losses)
        self.current_step = 0
        self.current_amount = base_amount
        
    async def run(self, max_trades=10, interval=70, initial_direction=OperationType.CALL):
        """Run the Martingale strategy"""
        if not await self.check_asset_availability():
            return
            
        print(colored("[INFO]: ", "blue"), f"Starting Martingale strategy on {self.asset}")
        print(colored("[INFO]: ", "blue"), f"Parameters: Base amount=${self.base_amount}, Max step={self.max_step}")
        
        trades_executed = 0
        current_direction = initial_direction
        
        while trades_executed < max_trades:
            print(colored("[INFO]: ", "blue"), f"Trade {trades_executed+1}/{max_trades}, Amount: ${self.current_amount}")
            
            # Execute trade with current amount
            self.amount = self.current_amount
            win, profit = await self.execute_trade(current_direction)
            trades_executed += 1
            
            if win:
                # Reset on win
                self.current_step = 0
                self.current_amount = self.base_amount
                # Optionally flip direction after win
                current_direction = OperationType.PUT if current_direction == OperationType.CALL else OperationType.CALL
                print(colored("[STRATEGY]: ", "green"), f"Win! Resetting to base amount ${self.base_amount}")
            else:
                # Increase step on loss
                self.current_step += 1
                if self.current_step >= self.max_step:
                    # Reset after reaching max step
                    print(colored("[STRATEGY]: ", "yellow"), f"Reached max step ({self.max_step}). Resetting to base amount.")
                    self.current_step = 0
                    self.current_amount = self.base_amount
                else:
                    # Double the amount (classic Martingale)
                    self.current_amount = self.base_amount * (2 ** self.current_step)
                    print(colored("[STRATEGY]: ", "red"), f"Loss! Increasing amount to ${self.current_amount}")
            
            # Wait before next trade
            print(colored("[INFO]: ", "blue"), f"Waiting {interval} seconds before next trade...")
            await asyncio.sleep(interval)
            
        print(colored("[INFO]: ", "cyan"), "Strategy completed")
        print(colored("[SUMMARY]: ", "cyan"), f"Total trades: {self.wins + self.losses}")
        print(colored("[SUMMARY]: ", "cyan"), f"Wins: {self.wins}, Losses: {self.losses}")
        print(colored("[SUMMARY]: ", "cyan"), f"Win rate: {(self.wins / max(1, self.wins + self.losses)) * 100:.2f}%")
        print(colored("[SUMMARY]: ", "cyan"), f"Total profit: ${self.total_profit}") 