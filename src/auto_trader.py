import os
import sys
import asyncio
from dotenv import load_dotenv
from termcolor import colored

from quotexpy import Quotex
from quotexpy.utils import asrun
from quotexpy.utils.account_type import AccountType

from trading_strategies import (
    SimpleMovingAverageStrategy,
    RSIStrategy,
    MartingaleStrategy
)

# Load environment variables
load_dotenv()

# Get credentials from environment variables
EMAIL = os.getenv("QUOTEX_EMAIL")
PASSWORD = os.getenv("QUOTEX_PASSWORD")


def on_pin_code() -> str:
    """Handle 2FA pin code if required"""
    code = input("Enter the code sent to your email: ")
    return code


# Initialize Quotex client
client = Quotex(
    email=EMAIL,
    password=PASSWORD,
    headless=True,
    on_pin_code=on_pin_code,
)


async def run_sma_strategy():
    """Run the Simple Moving Average strategy"""
    check_connect = await client.connect()
    if check_connect:
        print(colored("[INFO]: ", "blue"), "Connected to Quotex")
        client.change_account(AccountType.PRACTICE)
        
        # Configuration parameters
        asset = input("Enter asset (default: EURUSD): ") or "EURUSD"
        amount = float(input("Enter trade amount (default: 1): ") or "1")
        duration = int(input("Enter duration in seconds (default: 60): ") or "60")
        short_period = int(input("Enter short MA period (default: 5): ") or "5")
        long_period = int(input("Enter long MA period (default: 20): ") or "20")
        max_trades = int(input("Enter max trades (default: 5): ") or "5")
        
        # Create and run the strategy
        strategy = SimpleMovingAverageStrategy(
            client=client,
            asset=asset,
            amount=amount,
            duration=duration,
            short_period=short_period,
            long_period=long_period
        )
        
        await strategy.run(max_trades=max_trades)
    else:
        print(colored("[ERROR]: ", "red"), "Failed to connect to Quotex")
    
    client.close()


async def run_rsi_strategy():
    """Run the RSI strategy"""
    check_connect = await client.connect()
    if check_connect:
        print(colored("[INFO]: ", "blue"), "Connected to Quotex")
        client.change_account(AccountType.PRACTICE)
        
        # Configuration parameters
        asset = input("Enter asset (default: EURUSD): ") or "EURUSD"
        amount = float(input("Enter trade amount (default: 1): ") or "1")
        duration = int(input("Enter duration in seconds (default: 60): ") or "60")
        rsi_period = int(input("Enter RSI period (default: 14): ") or "14")
        oversold = int(input("Enter oversold threshold (default: 30): ") or "30")
        overbought = int(input("Enter overbought threshold (default: 70): ") or "70")
        max_trades = int(input("Enter max trades (default: 5): ") or "5")
        
        # Create and run the strategy
        strategy = RSIStrategy(
            client=client,
            asset=asset,
            amount=amount,
            duration=duration,
            rsi_period=rsi_period,
            oversold=oversold,
            overbought=overbought
        )
        
        await strategy.run(max_trades=max_trades)
    else:
        print(colored("[ERROR]: ", "red"), "Failed to connect to Quotex")
    
    client.close()


async def run_martingale_strategy():
    """Run the Martingale strategy"""
    check_connect = await client.connect()
    if check_connect:
        print(colored("[INFO]: ", "blue"), "Connected to Quotex")
        client.change_account(AccountType.PRACTICE)
        
        # Configuration parameters
        asset = input("Enter asset (default: EURUSD): ") or "EURUSD"
        base_amount = float(input("Enter base amount (default: 1): ") or "1")
        duration = int(input("Enter duration in seconds (default: 60): ") or "60")
        max_step = int(input("Enter max step (default: 4): ") or "4")
        max_trades = int(input("Enter max trades (default: 10): ") or "10")
        direction = input("Enter initial direction (CALL/PUT, default: CALL): ").upper() or "CALL"
        
        # Create and run the strategy
        from quotexpy.utils.operation_type import OperationType
        initial_direction = OperationType.CALL if direction == "CALL" else OperationType.PUT
        
        strategy = MartingaleStrategy(
            client=client,
            asset=asset,
            base_amount=base_amount,
            duration=duration,
            max_step=max_step
        )
        
        await strategy.run(max_trades=max_trades, initial_direction=initial_direction)
    else:
        print(colored("[ERROR]: ", "red"), "Failed to connect to Quotex")
    
    client.close()


async def main():
    """Main function to drive the program"""
    if not EMAIL or not PASSWORD:
        print(colored("[ERROR]: ", "red"), "Email or password not set. Please check your .env file.")
        return
    
    print(colored("=== Quotex Automated Trading Bot ===", "cyan"))
    print("1. Run Simple Moving Average (SMA) Strategy")
    print("2. Run Relative Strength Index (RSI) Strategy")
    print("3. Run Martingale Strategy")
    print("0. Exit")
    
    choice = input("\nEnter your choice: ")
    
    if choice == "1":
        await run_sma_strategy()
    elif choice == "2":
        await run_rsi_strategy()
    elif choice == "3":
        await run_martingale_strategy()
    elif choice == "0":
        print(colored("[INFO]: ", "blue"), "Exiting...")
        return
    else:
        print(colored("[ERROR]: ", "red"), "Invalid choice")


if __name__ == "__main__":
    try:
        asrun(main())
    except KeyboardInterrupt:
        print(colored("[INFO]: ", "blue"), "Program terminated by user")
        sys.exit(0)
    except Exception as e:
        print(colored("[ERROR]: ", "red"), f"An error occurred: {str(e)}")
        sys.exit(1) 