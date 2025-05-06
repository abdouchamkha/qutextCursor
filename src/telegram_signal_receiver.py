import os
import sys
import json
import asyncio
import logging
from dotenv import load_dotenv
from termcolor import colored

# Add Telegram bot API
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import our trade executor
from trade_executor import execute_from_signal
from quotexpy.asyncio import run  # Import run instead of asrun

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Telegram token from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_CHAT_IDS = [int(id.strip()) for id in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if id.strip()]

# Signal parsing keywords
SIGNAL_KEYWORDS = ['CALL', 'PUT', 'BUY', 'SELL']

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    await update.message.reply_text(
        "Welcome to Quotex Trade Executor Bot!\n\n"
        "I can execute trades on Quotex based on signals you send.\n\n"
        "Format your signals like this:\n"
        "EURUSD CALL 1 60\n"
        "(asset action amount duration)"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_CHAT_IDS:
        return
    
    await update.message.reply_text(
        "How to use this bot:\n\n"
        "1. Send trade signals in this format:\n"
        "   EURUSD CALL 1 60\n"
        "   (asset action amount duration)\n\n"
        "2. Available commands:\n"
        "   /start - Start the bot\n"
        "   /help - Show this help message\n"
        "   /balance - Check current balance\n"
        "   /assets - List available assets\n\n"
        "3. Signal format details:\n"
        "   - Asset: Trading pair (e.g., EURUSD, GBPJPY)\n"
        "   - Action: CALL/PUT (or BUY/SELL)\n"
        "   - Amount: Trade amount in dollars\n"
        "   - Duration: Trade duration in seconds"
    )

async def parse_signal(text):
    """Parse signal text into trade parameters"""
    # Simple parsing logic - can be made more sophisticated
    parts = text.strip().split()
    
    if len(parts) < 2:
        return None
    
    # Find the action keyword
    action_idx = -1
    for i, part in enumerate(parts):
        if part.upper() in SIGNAL_KEYWORDS:
            action_idx = i
            break
    
    if action_idx == -1:
        return None
    
    # Extract parameters
    try:
        asset = parts[action_idx - 1].upper() if action_idx > 0 else "EURUSD"
        action = parts[action_idx].upper()
        
        # Map BUY to CALL and SELL to PUT if needed
        if action == "BUY":
            action = "CALL"
        elif action == "SELL":
            action = "PUT"
        
        # Try to get amount and duration if provided
        amount = float(parts[action_idx + 1]) if len(parts) > action_idx + 1 else 1
        duration = int(parts[action_idx + 2]) if len(parts) > action_idx + 2 else 60
        
        return {
            'asset': asset,
            'action': action,
            'amount': amount,
            'duration': duration
        }
    except (IndexError, ValueError):
        return {
            'asset': asset,
            'action': action,
            'amount': 1,
            'duration': 60
        }

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming messages and execute trades based on signals."""
    user_id = update.effective_user.id
    if user_id not in ALLOWED_CHAT_IDS:
        logger.info(f"Unauthorized access attempt from user {user_id}")
        return
    
    text = update.message.text
    logger.info(f"Received message: {text}")
    
    # Check if message contains a signal
    signal_data = await parse_signal(text)
    
    if signal_data:
        # Acknowledge signal receipt
        await update.message.reply_text(
            f"📊 Signal detected!\n"
            f"Asset: {signal_data['asset']}\n"
            f"Action: {signal_data['action']}\n"
            f"Amount: ${signal_data['amount']}\n"
            f"Duration: {signal_data['duration']}s\n\n"
            f"Executing trade..."
        )
        
        # Execute the trade
        try:
            loop = asyncio.get_event_loop()
            result, profit = await execute_from_signal(signal_data)
            
            if result:
                await update.message.reply_text(
                    f"✅ Trade successful!\n"
                    f"Profit: ${profit}"
                )
            else:
                await update.message.reply_text(
                    f"❌ Trade unsuccessful.\n"
                    f"Loss: ${abs(profit) if profit else 'Unknown'}"
                )
        
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            await update.message.reply_text(f"❌ Error executing trade: {str(e)}")
    else:
        # No valid signal found
        if any(keyword in text.upper() for keyword in SIGNAL_KEYWORDS):
            await update.message.reply_text(
                "⚠️ Signal format not recognized. Please use format:\n"
                "EURUSD CALL 1 60\n"
                "(asset action amount duration)"
            )

def main():
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        print(colored("[ERROR]: ", "red"), "TELEGRAM_TOKEN not set. Please add it to your .env file.")
        return
    
    if not ALLOWED_CHAT_IDS:
        print(colored("[WARNING]: ", "yellow"), "ALLOWED_CHAT_IDS not set. No users will be able to use the bot.")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    print(colored("[INFO]: ", "blue"), "Starting bot...")
    application.run_polling()
    
    print(colored("[INFO]: ", "blue"), "Bot stopped")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("[INFO]: ", "blue"), "Bot terminated by user")
        sys.exit(0)
    except Exception as e:
        print(colored("[ERROR]: ", "red"), f"An error occurred: {str(e)}")
        sys.exit(1) 