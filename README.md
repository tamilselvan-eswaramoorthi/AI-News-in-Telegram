# AI News Bot for Telegram

A Python bot that fetches the latest AI news from [smol.ai](https://news.smol.ai) and sends summarized updates to a Telegram group using Google's Gemini API.

## Features

- 🤖 Automatically fetches the latest AI news from smol.ai
- 📝 Summarizes news items using Google Gemini AI
- 📱 Sends formatted messages to Telegram groups
- ☁️ Deployable as a Google Cloud Function
- 💾 Stores send records in BigQuery
- 🔄 Tracks sent news to avoid duplicates

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
# Required for all deployments
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export GEMINI_API_KEY="your_gemini_api_key"

# For BigQuery (Production)
export USE_BIGQUERY="true"
export GCP_PROJECT_ID="your-gcp-project-id"
export BIGQUERY_DATASET="ai_news_bot"  # Optional, defaults to "ai_news_bot"
export BIGQUERY_TABLE="sent_dates"      # Optional, defaults to "sent_dates"
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
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token,TELEGRAM_CHAT_ID=your_chat_id,GEMINI_API_KEY=your_api_key,USE_BIGQUERY=true,GCP_PROJECT_ID=your-project-id
```

### BigQuery Setup

When using BigQuery (recommended for production):

1. **The bot will automatically create**:
   - Dataset: `ai_news_bot` (or your custom name)
   - Table: `sent_dates` (or your custom name)
   - Schema: `date` (STRING), `timestamp` (TIMESTAMP), `status` (STRING)

2. **Ensure your Cloud Function has BigQuery permissions**:
   - The service account needs `BigQuery Data Editor` role
   - Or grant specific permissions: `bigquery.datasets.create`, `bigquery.tables.create`, `bigquery.tables.updateData`

3. **To use custom dataset/table names**, set environment variables:
   ```bash
   export BIGQUERY_DATASET="my_custom_dataset"
   export BIGQUERY_TABLE="my_custom_table"
   ```

## How It Works

1. **Initialization**: 
   - Loads configuration from environment variables
   - Connects to BigQuery (or CSV for local testing)
   - Creates database tables if they don't exist

2. **News Fetching**:
   - Processes all dates in the current week (Monday to Sunday)
   - Checks database to skip already-sent news
   - Scrapes the latest AI news issue from news.smol.ai

3. **Processing**:
   - Extracts the AI Twitter Recap section
   - Parses news items and categories
   - Summarizes each item using Gemini AI to concise bullet points

4. **Delivery**:
   - Sends formatted messages to the configured Telegram group
   - Logs successful sends to BigQuery with timestamp and status
   - Returns summary of sent/skipped/not found items

## Configuration

### Required Environment Variables

- **TELEGRAM_BOT_TOKEN**: Your Telegram bot token from BotFather
- **TELEGRAM_CHAT_ID**: The ID of your Telegram group/chat
- **GEMINI_API_KEY**: Your Google Gemini API key

### Database Configuration

- **USE_BIGQUERY**: Set to `true` for BigQuery, `false` for CSV (default: `true`)
- **GCP_PROJECT_ID**: Your GCP project ID (required when USE_BIGQUERY=true)
- **BIGQUERY_DATASET**: BigQuery dataset name (default: `ai_news_bot`)
- **BIGQUERY_TABLE**: BigQuery table name (default: `sent_dates`)
- **CSV_FILE**: CSV file path for local testing (default: `sent_dates.csv`)

## Dependencies

- `functions-framework` - For Google Cloud Functions support
- `requests` - HTTP requests
- `python-telegram-bot` - Telegram API wrapper
- `beautifulsoup4` - HTML parsing
- `google-genai` - Google Gemini AI API
- `google-cloud-bigquery` - BigQuery client library

## Project Structure

```
AI-News-in-whatapp/
├── main.py              # Main bot logic and Cloud Function entry point
├── config.py            # Configuration management
├── database.py          # Database interface (BigQuery & CSV implementations)
├── requirements.txt     # Python dependencies
├── sent_dates.csv       # Local CSV storage (when USE_BIGQUERY=false)
└── README.md           # This file
```

## Database Schema

### BigQuery Table: `sent_dates`

| Column    | Type      | Mode     | Description                    |
|-----------|-----------|----------|--------------------------------|
| date      | STRING    | REQUIRED | Date in YY-MM-DD format        |
| timestamp | TIMESTAMP | REQUIRED | When the news was sent         |
| status    | STRING    | NULLABLE | Status of the send operation   |

## License

MIT
