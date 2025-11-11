import os
import requests
import telegram
import asyncio
import traceback
import csv
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from google import genai
from google.genai import types
import functions_framework

class AINewsBot:
    def __init__(self):
        self.bot_token = str(os.getenv("TELEGRAM_BOT_TOKEN"))
        self.chat_id = str(os.getenv("TELEGRAM_CHAT_ID"))
        self.gemini_api_key = str(os.getenv("GEMINI_API_KEY"))

        self.base_url = "https://news.smol.ai"
        self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        self.csv_file = "sent_dates.csv"
    
    def get_week_dates(self):
        """Get all dates for the current week (Monday to Sunday)"""
        today = datetime.now()
        # Get Monday of current week (0 = Monday, 6 = Sunday)
        monday = today - timedelta(days=today.weekday())
        
        week_dates = []
        for i in range(7):
            date = monday + timedelta(days=i)
            week_dates.append(date.strftime("%y-%m-%d"))
        
        return week_dates
    
    def is_date_sent(self, date_str):
        """Check if news for this date has already been sent"""
        try:
            if not os.path.exists(self.csv_file):
                return False
            
            with open(self.csv_file, 'r', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0] == date_str:
                        return True
            return False
        except Exception as e:
            print(f"Error checking sent dates: {e}")
            return False
    
    def log_sent_date(self, date_str):
        """Log the date when news was successfully sent"""
        try:
            file_exists = os.path.exists(self.csv_file)
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['date', 'timestamp'])
                writer.writerow([date_str, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            print(f"Logged sent date: {date_str}")
        except Exception as e:
            print(f"Error logging sent date: {e}")
    
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
                            text=f"Summarize the following AI news item in exactly 2 concise lines add href (example <a href='https://www.google.com/'>Google</a>) to highlight urls:\n\n{text}"
                        ),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0,
                ),
            )

            response_text = ""
            for chunk in self.gemini_client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text
            
            return response_text.strip()
        except Exception as e:
            print(f"Error summarizing with Gemini: {e}")
            return text  # Return original text if summarization fails

    async def send_to_telegram_group(self, heading, items):
        try:
            bot = telegram.Bot(token=self.bot_token)
            
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Format message with HTML
            message = f"<b>{heading}</b>\n"
            message += "━━━━━━━━━━━━━━\n\n"
            
            for idx, item in enumerate(items, 1):
                item_text = item.get_text().strip()
                # Summarize each item to 2 lines
                if idx == len(items):
                    summarized_text = item_text
                else:
                    summarized_text = self.summarize_with_gemini(item_text)
                message += f"{idx}. {summarized_text}\n\n"
                        
            await bot.send_message(
                chat_id=self.chat_id, 
                text=message,
                parse_mode='HTML'
            )
            print(f"Message successfully sent at {current_time}")

        except telegram.error.InvalidToken:
            print("ERROR: Bot token is invalid. Please check your BOT_TOKEN.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"An unexpected error occurred: {e}")
    
    async def run_async(self, curr_date):
        """Async version of run method"""
        # Check if news for this date has already been sent
        if self.is_date_sent(curr_date):
            print(f"News for {curr_date} has already been sent. Skipping.")
            return False
        
        latest_issue = self.get_latest_issue(curr_date)
        if latest_issue:
            ai_recap = self.get_ai_recap(latest_issue)
            if ai_recap:
                parsed_recap = self.parse_ai_recap(ai_recap)
                for heading, items in parsed_recap.items():
                    await self.send_to_telegram_group(heading, items)
                
                # Log the date after successful send
                self.log_sent_date(curr_date)
                return True
        return False

    def run(self):
        latest_issue = self.get_latest_issue()
        if latest_issue:
            ai_recap = self.get_ai_recap(latest_issue)
            if ai_recap:
                parsed_recap = self.parse_ai_recap(ai_recap)
                for heading, items in parsed_recap.items():
                    asyncio.run(self.send_to_telegram_group(heading, items))
                return True
        return False

@functions_framework.http
def run_ai_news_bot(request):
    """HTTP Cloud Function to run the AI News Bot.
    Args:
        request (flask.Request): The request object.
    Returns:
        The response text indicating success or failure.
    """
    try:
        bot = AINewsBot()
        week_dates = bot.get_week_dates()
        
        sent_count = 0
        skipped_count = 0
        not_found_count = 0
        results = []
        
        for curr_date in week_dates:
            print(f"\n--- Checking news for {curr_date} ---")
            
            # Check if already sent
            if bot.is_date_sent(curr_date):
                print(f"News for {curr_date} has already been sent. Skipping.")
                skipped_count += 1
                results.append(f"{curr_date}: Already sent (skipped)")
                continue
            
            # Try to fetch and send news
            success = asyncio.run(bot.run_async(curr_date))
            
            if success:
                sent_count += 1
                results.append(f"{curr_date}: Successfully sent")
            else:
                not_found_count += 1
                results.append(f"{curr_date}: No news found")
        
        summary = {
            'status': 'success',
            'message': f'Week processing complete. Sent: {sent_count}, Skipped: {skipped_count}, Not found: {not_found_count}',
            'results': results
        }
        
        return summary, 200
            
    except Exception as e:
        traceback.print_exc()
        return {'status': 'error', 'message': f'An error occurred: {str(e)}'}, 500