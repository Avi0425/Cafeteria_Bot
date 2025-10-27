# Railway Deployment Guide

## Quick Start

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push
```

### 2. Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### 3. Configure Environment Variables

In your Railway project dashboard:
- Go to the "Variables" tab
- Add these 4 environment variables:

```
TELEGRAM_BOT_TOKEN = <your telegram bot token>
TELEGRAM_CHAT_ID = <your telegram chat id>
USER_EMAIL = <your bennett email>
USER_PASSWORD = <your bennett password>
```

### 4. Deploy

Railway will automatically:
1. Detect the `Procfile`
2. Install dependencies from `requirements.txt`
3. Use the Python version from `runtime.txt`
4. Start your bot

## How It Works

- The bot runs immediately when deployed
- Runs again daily at 8:00 AM IST (configurable)
- Sends you a complete report via Telegram

## Monitoring

Check the Railway logs to see:
- When the bot runs
- Any errors that occur
- Telegram notifications being sent

## Cost

Railway offers a free tier that should be sufficient for this bot.

## Troubleshooting

### Bot not sending messages
- Check that `TELEGRAM_CHAT_ID` is correct
- Verify bot token is valid

### Login fails
- Check that credentials are correct
- Ensure no special characters need escaping

### Bot stops running
- Check Railway logs for errors
- Verify environment variables are set correctly

