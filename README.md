# AI News Bot for Telegram

A Python bot that fetches the latest AI news from [smol.ai](https://news.smol.ai) and sends summarized updates to a Telegram group using Google's Gemini API.

## Features

- 🤖 Automatically fetches the latest AI news from smol.ai
- 📝 Summarizes news items using Google Gemini AI
- 📱 Sends formatted messages to Telegram groups
- ☁️ Deployable as a Google Cloud Function

## Prerequisites

- Python 3.x
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Telegram Chat ID
- Google Gemini API Key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI-News-in-whatapp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export GEMINI_API_KEY="your_gemini_api_key"
```

## Usage

### Run Locally

```bash
python main.py
```

### Deploy as Google Cloud Function

The bot is designed to run as an HTTP Cloud Function. Deploy using:

```bash
gcloud functions deploy run_ai_news_bot \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token,TELEGRAM_CHAT_ID=your_chat_id,GEMINI_API_KEY=your_api_key
```

## How It Works

1. Scrapes the latest AI news issue from news.smol.ai
2. Extracts the AI Twitter Recap section
3. Parses news items and categories
4. Summarizes each item using Gemini AI to 2 concise lines
5. Sends formatted messages to the configured Telegram group

## Configuration

- **TELEGRAM_BOT_TOKEN**: Your Telegram bot token from BotFather
- **TELEGRAM_CHAT_ID**: The ID of your Telegram group/chat
- **GEMINI_API_KEY**: Your Google Gemini API key

## Dependencies

- `functions-framework` - For Google Cloud Functions support
- `requests` - HTTP requests
- `python-telegram-bot` - Telegram API wrapper
- `beautifulsoup4` - HTML parsing
- `google-genai` - Google Gemini AI API

## License

MIT
