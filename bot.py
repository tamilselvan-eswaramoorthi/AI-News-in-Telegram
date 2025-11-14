import requests
import telegram
import asyncio
import traceback
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from google import genai
from google.genai import types

from config import Config
from database import get_database

class AINewsBot:
    def __init__(self):
        self.config = Config()
        
        # Initialize components
        self.bot_token = self.config.telegram_bot_token
        self.chat_id = self.config.telegram_chat_id
        self.base_url = self.config.base_url
        self.gemini_client = genai.Client(api_key=self.config.gemini_api_key)
        self.db = get_database()
    
    def get_week_dates(self):
        """Get all dates for the current week (Monday to Sunday)"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        
        week_dates = []
        for i in range(7):
            date = monday + timedelta(days=i)
            week_dates.append(date.strftime("%y-%m-%d"))
        
        return week_dates
    
    def get_latest_issue(self, curr_date):
        response = requests.get(self.base_url + '/issues')
        soup = BeautifulSoup(response.text, 'html.parser')
        issue_links = soup.find_all('a', href=True)
        for link in issue_links:
            href = link['href']
            if href.startswith(f'/issues/{curr_date}-'):
                issue_number = href.strip()
                return f"{self.base_url}{issue_number}"
        return None

    def get_ai_recap(self, issue_url):
        response = requests.get(issue_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        ai_twitter_recap = soup.find(id='ai-twitter-recap')
        if ai_twitter_recap:
            ai_reddit_recap = soup.find(id='ai-reddit-recap')
            recap_content = ["""<!DOCTYPE html>
<html>
<body>"""]
            for sibling in ai_twitter_recap.next_siblings:
                if sibling == ai_reddit_recap:
                    break
                recap_content.append(str(sibling))
            recap_content.append("""</body>
</html>""")
            return ''.join(recap_content)
        return None

    def parse_ai_recap(self, ai_recap_html):
        soup = BeautifulSoup(ai_recap_html, 'html.parser')
        items = soup.find_all('p')
        recap_dict = {}
        for item in items:
            text = item.get_text().strip()
            if text:
                recap_dict[text] = []
                #find the next ul sibling
                ul = item.find_next_sibling('ul')
                if ul:
                    for li in ul.find_all('li'):
                        recap_dict[text].append(li)
        return recap_dict

    def summarize_with_gemini(self, text):
        """Summarize text to 2 lines using Gemini API"""
        try:
            model = "gemini-flash-lite-latest"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=f"""Summarize the following AI news into bullet points, with each point limited to two lines.
Do not retain and highlight any links or mentions
Total response should be concise (200 words) and formatted for Telegram messages.
Do not add any commentary or extra text outside the summary.
use emoji's where appropriate

AI News: 
{text}

Summary:
"""
                        ),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig()
            response_text = ""
            for chunk in self.gemini_client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text
            
            return response_text.strip().replace("""```html""", "").replace("""```""", "")
        except Exception as e:
            print(f"Error summarizing with Gemini: {e}")
            return text  # Return original text if summarization fails

    async def send_to_telegram_group(self, parsed_recap, current_date):
        try:
            bot = telegram.Bot(token=self.bot_token)
            current_date = datetime.strptime(current_date, "%y-%m-%d").strftime("%d %b %Y")
            all_news = ''
            for heading, items in parsed_recap.items():
                all_news += f"<b>{heading}</b>\n"
                all_news += "━━━━━━━━━━━━━━\n\n"
                for idx, item in enumerate(items, 1):
                    item_text = item.get_text().strip()                        
                    all_news += f"{idx}. {item_text}\n\n"

            summarized_text = self.summarize_with_gemini(all_news)
            
            message = f"<b>AI News Recap for {current_date}</b>\n\n{summarized_text}"
                        
            await bot.send_message(
                chat_id=self.chat_id, 
                text=message,
                parse_mode='HTML'
            )
            print(f"Message successfully sent at {current_date}")

        except telegram.error.InvalidToken:
            print("ERROR: Bot token is invalid. Please check your BOT_TOKEN.")
        except Exception as e:
            traceback.print_exc()
            print(f"An unexpected error occurred: {e}")
    

    def run(self, curr_date):
        """
        Fetch and send AI news for a specific date
        """
        latest_issue = self.get_latest_issue(curr_date)
        if latest_issue:
            ai_recap = self.get_ai_recap(latest_issue)
            if ai_recap:
                parsed_recap = self.parse_ai_recap(ai_recap)
                asyncio.run(self.send_to_telegram_group(parsed_recap, curr_date))
                self.db.log_sent_date(curr_date, status="success")
                return True
        return False
