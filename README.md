# Cafeteria Bot

A Telegram bot that fetches daily attendance, timetable, and cafeteria menu information from Bennett University ERP and sends it to you via Telegram.

## Features

- **Daily Attendance Reports**: Get your overall and subject-wise attendance percentage
- **Timetable**: See today's class schedule
- **Cafeteria Menu**: Check what's on the menu for today

## Railway Deployment

### Prerequisites

1. A Railway account ([railway.app](https://railway.app))
2. A Telegram bot token ([@BotFather](https://t.me/BotFather))
3. Your Telegram chat ID
4. Your Bennett University credentials

### Deployment Steps

1. **Push to GitHub**: Push this repository to GitHub

2. **Connect to Railway**:
   - Go to [railway.app](https://railway.app)
   - Create a new project
   - Select "Deploy from GitHub"
   - Choose this repository

3. **Set Environment Variables**:
   In Railway dashboard, go to Variables and set:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   USER_EMAIL=your_bennett_email
   USER_PASSWORD=your_bennett_password
   ```

4. **Deploy**: Railway will automatically deploy your bot

### How It Works

- The bot runs once immediately when deployed
- It then checks every hour if it's time to run the scheduled daily report (8:00 AM IST by default)
- The report includes:
  - Today's timetable
  - Overall and subject-wise attendance
  - Today's cafeteria menu

### Schedule Configuration

To change when the report runs, edit the `run_hour` and `run_minute` variables in the `should_run_today()` function in `Cafeteria_Bot.py`:

```python
run_hour = 1   # 1 AM IST
run_minute = 0
```

## Local Development

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables or use the hardcoded fallback values (not recommended for production)
4. Run the bot:
   ```bash
   python Cafeteria_Bot.py
   ```

## Security Notes

- Never commit sensitive credentials to version control
- Use environment variables for all sensitive data
- Remove hardcoded credentials before deploying to production

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather | Yes |
| `TELEGRAM_CHAT_ID` | Your Telegram chat/user ID | Yes |
| `USER_EMAIL` | Your Bennett University email | Yes |
| `USER_PASSWORD` | Your Bennett University password | Yes |

## License

MIT


