import os
import sys
import time
import asyncio
from dotenv import load_dotenv
from termcolor import colored

from quotexpy import Quotex
from quotexpy.utils import asset_parse
# from quotexpy.asyncio import run
from quotexpy.utils.account_type import AccountType
from quotexpy.utils.operation_type import OperationType

# Load environment variables
load_dotenv()

# Get credentials from environment variables
EMAIL = os.getenv("QUOTEX_EMAIL")
PASSWORD = os.getenv("QUOTEX_PASSWORD")

# Default settings
DEFAULT_ASSET = "EURUSD"
DEFAULT_AMOUNT = 1
DEFAULT_DURATION = 60  # seconds


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


class TradeExecutor:
    """Class to handle trade execution and tracking"""
    
    def __init__(self, client):
        self.client = client
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_profit = 0
        self.active_trades = {}
    
    async def connect(self):
        """Connect to Quotex and set account type"""
        check_connect = await self.client.connect()
        if check_connect:
            print(colored("[INFO]: ", "blue"), "Connected to Quotex successfully")
            self.client.change_account(AccountType.PRACTICE)  # Use PRACTICE account by default
            return True
        else:
            print(colored("[ERROR]: ", "red"), "Failed to connect to Quotex")
            return False
    
    def check_asset(self, asset):
        """Check if an asset is open, try OTC version if closed"""
        asset_query = asset_parse(asset)
        asset_open = self.client.check_asset(asset_query)
        
        if not asset_open or not asset_open[2]:
            print(colored("[WARN]: ", "yellow"), f"Asset {asset} is closed.")
            otc_asset = f"{asset}_otc"
            print(colored("[WARN]: ", "yellow"), f"Trying OTC Asset -> {otc_asset}")
            asset_query = asset_parse(otc_asset)
            asset_open = self.client.check_asset(asset_query)
            
            if asset_open and asset_open[2]:
                return otc_asset, asset_open
            else:
                print(colored("[ERROR]: ", "red"), f"No available version of {asset} found.")
                return None, None
        
        return asset, asset_open
    
    async def execute_trade(self, asset, amount, action, duration):
        """Execute a trade with the given parameters"""
        # Check if asset is available
        asset_to_trade, asset_data = self.check_asset(asset)
        if not asset_to_trade or not asset_data or not asset_data[2]:
            print(colored("[ERROR]: ", "red"), f"Asset {asset} is not available for trading")
            return False, None
        
        print(colored("[INFO]: ", "blue"), f"Executing {action} trade on {asset_to_trade} for ${amount} with duration {duration}s")
        
        # Execute the trade
        status, trade_info = await self.client.trade(action, amount, asset_to_trade, duration)
        
        if status:
            trade_id = trade_info.get('id')
            print(colored("[INFO]: ", "blue"), f"Trade executed. ID: {trade_id}")
            self.active_trades[trade_id] = {
                'asset': asset_to_trade,
                'amount': amount,
                'action': action,
                'duration': duration,
                'entry_time': time.time(),
                'expiry_time': time.time() + duration,
                'status': 'active'
            }
            return True, trade_info
        else:
            print(colored("[ERROR]: ", "red"), "Trade execution failed")
            return False, None
    
    async def check_trade_result(self, trade_id):
        """Check if a trade was successful"""
        if not trade_id:
            return False, 0
        
        print(colored("[INFO]: ", "blue"), f"Checking result for trade ID: {trade_id}")
        
        try:
            win = await self.client.check_win(trade_id)
            profit = self.client.get_profit()
            
            if win:
                self.wins += 1
                self.total_profit += profit
                print(colored("[RESULT]: ", "green"), f"Win! Profit: ${profit}")
                result = True
            else:
                self.losses += 1
                self.total_profit -= abs(profit)
                print(colored("[RESULT]: ", "red"), f"Loss! Amount: ${abs(profit)}")
                result = False
            
            self.total_trades += 1
            win_rate = (self.wins / self.total_trades) * 100 if self.total_trades > 0 else 0
            
            print(colored("[STATS]: ", "cyan"), f"Wins: {self.wins}, Losses: {self.losses}, Win Rate: {win_rate:.2f}%, Total Profit: ${self.total_profit}")
            
            # Update trade status
            if trade_id in self.active_trades:
                self.active_trades[trade_id]['status'] = 'win' if win else 'loss'
                self.active_trades[trade_id]['profit'] = profit
            
            return result, profit
            
        except Exception as e:
            print(colored("[ERROR]: ", "red"), f"Error checking trade result: {str(e)}")
            return False, 0
    
    async def get_balance(self):
        """Get current account balance"""
        try:
            balance = await self.client.get_balance()
            print(colored("[INFO]: ", "blue"), f"Current balance: ${balance}")
            return balance
        except Exception as e:
            print(colored("[ERROR]: ", "red"), f"Error getting balance: {str(e)}")
            return None
    
    async def list_available_assets(self):
        """List all available assets for trading"""
        print(colored("[INFO]: ", "blue"), "Listing available assets:")
        available_assets = []
        
        try:
            all_assets = self.client.get_all_asset_name()
            for asset_name in all_assets:
                asset_status = self.client.check_asset(asset_name)
                if asset_status and asset_status[2]:  # Check if asset is open
                    available_assets.append(asset_name)
                    print(colored("[ASSET]: ", "green"), asset_name)
            
            print(colored("[INFO]: ", "blue"), f"Total available assets: {len(available_assets)}")
            return available_assets
        except Exception as e:
            print(colored("[ERROR]: ", "red"), f"Error listing assets: {str(e)}")
            return []
    
    def close(self):
        """Close the connection"""
        self.client.close()
        print(colored("[INFO]: ", "blue"), "Connection closed")


async def main():
    """Main function to manage trade execution"""
    if not EMAIL or not PASSWORD:
        print(colored("[ERROR]: ", "red"), "Email or password not set. Please check your .env file.")
        return
    
    executor = TradeExecutor(client)
    
    # Connect to Quotex
    if not await executor.connect():
        return
    
    # Get initial balance
    await executor.get_balance()
    
    print(colored("=== Quotex Trade Executor ===", "cyan"))
    print("1. Execute a single trade")
    print("2. List available assets")
    print("3. Check account balance")
    print("0. Exit")
    
    choice = input("\nEnter your choice: ")
    
    if choice == "1":
        # Execute a single trade for testing
        asset = input("Enter asset (default: EURUSD): ") or DEFAULT_ASSET
        amount = float(input("Enter amount (default: 1): ") or DEFAULT_AMOUNT)
        action_input = input("Enter action (CALL/PUT, default: CALL): ").upper() or "CALL"
        action = OperationType.CALL if action_input == "CALL" else OperationType.PUT
        duration = int(input("Enter duration in seconds (default: 60): ") or DEFAULT_DURATION)
        
        success, trade_info = await executor.execute_trade(asset, amount, action, duration)
        
        if success:
            # Wait for trade to complete
            trade_id = trade_info.get('id')
            wait_time = duration + 2  # Add a couple seconds buffer
            
            print(colored("[INFO]: ", "blue"), f"Waiting {wait_time} seconds for trade to complete...")
            await asyncio.sleep(wait_time)
            
            # Check result
            await executor.check_trade_result(trade_id)
    
    elif choice == "2":
        # List available assets
        await executor.list_available_assets()
    
    elif choice == "3":
        # Check account balance
        await executor.get_balance()
    
    elif choice == "0":
        print(colored("[INFO]: ", "blue"), "Exiting...")
    
    else:
        print(colored("[ERROR]: ", "red"), "Invalid choice")
    
    # Close connection
    executor.close()


# Example of how to execute a trade from an external signal
async def execute_from_signal(signal_data):
    """Execute a trade based on signal data from external source (e.g., Telegram)
    
    Expected signal_data format:
    {
        'asset': 'EURUSD',
        'action': 'CALL',  # 'CALL' or 'PUT'
        'amount': 10,
        'duration': 60     # in seconds
    }
    """
    executor = TradeExecutor(client)
    
    # Connect to Quotex
    if not await executor.connect():
        return False, None
    
    # Parse the action
    action = OperationType.CALL if signal_data.get('action') == 'CALL' else OperationType.PUT
    
    # Execute the trade
    success, trade_info = await executor.execute_trade(
        signal_data.get('asset', DEFAULT_ASSET),
        signal_data.get('amount', DEFAULT_AMOUNT),
        action,
        signal_data.get('duration', DEFAULT_DURATION)
    )
    
    if success:
        # Wait for trade to complete
        trade_id = trade_info.get('id')
        wait_time = signal_data.get('duration', DEFAULT_DURATION) + 2  # Add buffer
        
        print(colored("[INFO]: ", "blue"), f"Waiting {wait_time} seconds for trade to complete...")
        await asyncio.sleep(wait_time)
        
        # Check result
        result, profit = await executor.check_trade_result(trade_id)
        
        # Close connection
        executor.close()
        
        return result, profit
    
    # Close connection
    executor.close()
    return False, None


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(colored("[INFO]: ", "blue"), "Program terminated by user")
        sys.exit(0)
    except Exception as e:
        print(colored("[ERROR]: ", "red"), f"An error occurred: {str(e)}")
        sys.exit(1) 