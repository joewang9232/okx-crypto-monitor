# OKX Crypto Monitor

Monitor OKX USDT perpetual contracts for 5-minute price swings >= 5%.
Alerts sent to Telegram in ~12 seconds for all 394 contracts.

## Quick Start

1. Create a Telegram Bot via @BotFather, get your token
2. Get your chat ID (send a message to your bot, check https://api.telegram.org/bot<TOKEN>/getUpdates)
3. Configure credentials:

```bash
# Option A: Environment variables (recommended for cron)
export TG_BOT_TOKEN="your_token"
export TG_CHAT_ID="your_chat_id"

# Option B: Config file
cp config.example.toml config.toml
# Edit config.toml with your credentials
```

4. Run: `python okx_5min_quick.py`

## Deploy with Cron

```bash
openclaw cron add --name "OKX Monitor" --cron "0,5,10 * * * *" --session isolated --message "TG_BOT_TOKEN=xxx TG_CHAT_ID=xxx python okx_5min_quick.py"
```

## Files

- `okx_5min_quick.py` - Main scanner (20 threads, ~12s scan)
- `config.example.toml` - Configuration template
- `README.md` - This file

## License

MIT
