# Quotex Trading Bot

A Python project for executing trades on the Quotex platform using the `quotexpy` library. This bot can be controlled via Telegram to execute trades based on signals.

## Features

- Connect to Quotex broker
- Execute trades manually or via Telegram signals
- Check trade results and track performance
- Get account balance
- List available assets
- Telegram bot integration for receiving trading signals

## Requirements

- Python 3.10 or higher
- `quotexpy` library
- Quotex account
- Telegram Bot API Token (for Telegram integration)

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd AutoLoginQutex
   ```

2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your credentials:
   ```
   QUOTEX_EMAIL=your_email@example.com
   QUOTEX_PASSWORD=your_password
   TELEGRAM_TOKEN=your_telegram_bot_token
   ALLOWED_CHAT_IDS=your_telegram_user_id,another_user_id
   ```

## Usage

### Manual Trade Execution

Run the trade executor script for manual trade execution:

```
python src/trade_executor.py
```

This provides the following options:
1. Execute a single trade
2. List available assets
3. Check account balance

### Telegram Bot Integration

Run the Telegram bot to receive and execute trades based on signals:

```
python src/telegram_signal_receiver.py
```

#### Telegram Signal Format

Send trade signals to your bot in the following format:
```
EURUSD CALL 1 60
```

Where:
- `EURUSD` is the asset
- `CALL` is the action (can be CALL/PUT or BUY/SELL)
- `1` is the amount to trade
- `60` is the duration in seconds

Example signals:
- `EURUSD CALL 5 60` - Buy EURUSD with $5 for 60 seconds
- `GBPJPY PUT 10 120` - Sell GBPJPY with $10 for 120 seconds

### Getting Your Telegram User ID

To get your Telegram User ID, you can:
1. Start a chat with @userinfobot on Telegram
2. Add this ID to your .env file in the ALLOWED_CHAT_IDS field

## Warning

Trading involves significant risk of loss and is not suitable for all investors. Only trade with money you can afford to lose and always practice on a demo account first.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

This project uses the `quotexpy` library by SantiiRepair. 