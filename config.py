import os

class Config:    
    # Telegram configuration
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    # Gemini AI configuration
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    # News source configuration
    base_url = "https://news.smol.ai"
    
    # Database configuration
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    bigquery_dataset = os.getenv("BIGQUERY_DATASET", "ai_news_bot")
    bigquery_table = os.getenv("BIGQUERY_TABLE", "sent_dates")

    gcp_key_path = os.getenv("GCP_KEY_PATH", "gcp_key.json")
