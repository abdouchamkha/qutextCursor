import os
import sys
import time
import asyncio
from dotenv import load_dotenv
from termcolor import colored

from quotexpy import Quotex
from quotexpy.utils import asset_parse, asrun
from quotexpy.utils.account_type import AccountType
from quotexpy.utils.candles_period import CandlesPeriod
from quotexpy.utils.operation_type import OperationType

# Load environment variables
load_dotenv()

# Get credentials from environment variables
EMAIL = os.getenv("QUOTEX_EMAIL")
PASSWORD = os.getenv("QUOTEX_PASSWORD")

# Default asset
DEFAULT_ASSET = "EURUSD"


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


def check_asset(asset):
    """Check if an asset is open, try OTC version if closed"""
    asset_query = asset_parse(asset)
    asset_open = client.check_asset(asset_query)
    if not asset_open or not asset_open[2]:
        print(colored("[WARN]: ", "yellow"), "Asset is closed.")
        asset = f"{asset}_otc"
        print(colored("[WARN]: ", "yellow"), "Try OTC Asset -> " + asset)
        asset_query = asset_parse(asset)
        asset_open = client.check_asset(asset_query)
    return asset, asset_open


async def get_balance():
    """Get and display the current balance"""
    check_connect = await client.connect()
    if check_connect:
        print(colored("[INFO]: ", "blue"), "Connection successful")
        client.change_account(AccountType.PRACTICE)
        balance = await client.get_balance()
        print(colored("[INFO]: ", "blue"), f"Balance: {balance}")
        return balance
    else:
        print(colored("[ERROR]: ", "red"), "Connection failed")
        return None


async def list_assets():
    """List all available assets and their status"""
    check_connect = await client.connect()
    if check_connect:
        print(colored("[INFO]: ", "blue"), "Available assets:")
        for asset_name in client.get_all_asset_name():
            asset_status = client.check_asset(asset_name)
            status = "OPEN" if asset_status and asset_status[2] else "CLOSED"
            print(f"{asset_name}: {status}")
    else:
        print(colored("[ERROR]: ", "red"), "Connection failed")
    client.close()


async def get_candle_data(asset=DEFAULT_ASSET, period=CandlesPeriod.ONE_MINUTE):
    """Retrieve candle data for analysis"""
    check_connect = await client.connect()
    if check_connect:
        asset, asset_open = check_asset(asset)
        if asset_open and asset_open[2]:
            print(colored("[INFO]: ", "blue"), f"Getting candle data for {asset}")
            candles = await client.get_candle_v2(asset, period)
            return candles
        else:
            print(colored("[WARN]: ", "yellow"), f"Asset {asset} is closed")
            return None
    else:
        print(colored("[ERROR]: ", "red"), "Connection failed")
        return None
    client.close()


async def execute_trade(asset=DEFAULT_ASSET, amount=1, action=OperationType.CALL, duration=60):
    """Execute a trade with the given parameters"""
    check_connect = await client.connect()
    if check_connect:
        client.change_account(AccountType.PRACTICE)
        print(colored("[INFO]: ", "blue"), f"Current balance: {await client.get_balance()}")
        
        asset, asset_open = check_asset(asset)
        if asset_open and asset_open[2]:
            print(colored("[INFO]: ", "blue"), f"Executing {action} trade on {asset} for ${amount}")
            status, trade_info = await client.trade(action, amount, asset, duration)
            
            if status:
                print(colored("[INFO]: ", "blue"), f"Trade executed. ID: {trade_info.get('id', 'Unknown')}")
                print(colored("[INFO]: ", "blue"), "Waiting for result...")
                
                if await client.check_win(trade_info.get('id')):
                    profit = client.get_profit()
                    print(colored("[INFO]: ", "green"), f"Win -> Profit: ${profit}")
                    return True, profit
                else:
                    loss = client.get_profit()
                    print(colored("[INFO]: ", "red"), f"Loss -> Lost: ${loss}")
                    return False, loss
            else:
                print(colored("[ERROR]: ", "red"), "Trade execution failed")
                return False, 0
        else:
            print(colored("[ERROR]: ", "red"), f"Asset {asset} is closed")
            return False, 0
    else:
        print(colored("[ERROR]: ", "red"), "Connection failed")
        return False, 0
    client.close()


async def stream_realtime_candles(asset=DEFAULT_ASSET, list_size=10):
    """Stream and display real-time candle data"""
    check_connect = await client.connect()
    if check_connect:
        asset, asset_open = check_asset(asset)
        if asset_open and asset_open[2]:
            print(colored("[INFO]: ", "blue"), f"Starting candle stream for {asset}")
            client.start_candles_stream(asset, list_size)
            
            # Wait until we have enough candles
            while True:
                candles = client.get_realtime_candles(asset)
                if len(candles) == list_size:
                    break
                await asyncio.sleep(0.5)
            
            # Display candles in real-time
            try:
                while True:
                    candles = client.get_realtime_candles(asset)
                    latest = candles[-1]
                    print(f"Latest candle: Open={latest[1]}, Close={latest[2]}, High={latest[3]}, Low={latest[4]}")
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print(colored("[INFO]: ", "blue"), "Stopping candle stream")
        else:
            print(colored("[ERROR]: ", "red"), f"Asset {asset} is closed")
    else:
        print(colored("[ERROR]: ", "red"), "Connection failed")
    client.close()


async def main():
    """Main function to drive the program"""
    if not EMAIL or not PASSWORD:
        print(colored("[ERROR]: ", "red"), "Email or password not set. Please check your .env file.")
        return
    
    print(colored("=== Quotex Trading Bot ===", "cyan"))
    print("1. Get account balance")
    print("2. List available assets")
    print("3. Execute a trade")
    print("4. Stream real-time candles")
    print("5. Get candle data")
    print("0. Exit")
    
    choice = input("\nEnter your choice: ")
    
    if choice == "1":
        await get_balance()
    elif choice == "2":
        await list_assets()
    elif choice == "3":
        asset = input("Enter asset (default: EURUSD): ") or DEFAULT_ASSET
        amount = float(input("Enter amount to trade: "))
        action_choice = input("Enter action (CALL/PUT): ").upper()
        action = OperationType.CALL if action_choice == "CALL" else OperationType.PUT
        duration = int(input("Enter duration in seconds: "))
        await execute_trade(asset, amount, action, duration)
    elif choice == "4":
        asset = input("Enter asset (default: EURUSD): ") or DEFAULT_ASSET
        await stream_realtime_candles(asset)
    elif choice == "5":
        asset = input("Enter asset (default: EURUSD): ") or DEFAULT_ASSET
        candles = await get_candle_data(asset)
        print(candles)
    elif choice == "0":
        print(colored("[INFO]: ", "blue"), "Exiting...")
        return
    else:
        print(colored("[ERROR]: ", "red"), "Invalid choice")
    
    client.close()


if __name__ == "__main__":
    try:
        asrun(main())
    except KeyboardInterrupt:
        print(colored("[INFO]: ", "blue"), "Program terminated by user")
        sys.exit(0)
    except Exception as e:
        print(colored("[ERROR]: ", "red"), f"An error occurred: {str(e)}")
        sys.exit(1) 