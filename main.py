import traceback
import functions_framework

from bot import AINewsBot

bot = AINewsBot()


@functions_framework.http
def run_ai_news_bot(request):
    try:
        week_dates = bot.get_week_dates()
        
        sent_count = 0
        skipped_count = 0
        not_found_count = 0
        results = []
        
        for curr_date in week_dates:
            print(f"\n--- Checking news for {curr_date} ---")
            
            # Check if already sent using database
            if bot.db.is_date_sent(curr_date):
                print(f"News for {curr_date} has already been sent. Skipping.")
                skipped_count += 1
                results.append(f"{curr_date}: Already sent (skipped)")
                continue
            
            # Try to fetch and send news
            success = bot.run(curr_date)
            
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

if __name__ == "__main__":
    # For local testing
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.route('/run_ai_news_bot', methods=['POST', "GET"])
    def handle_request():
        response, status_code = run_ai_news_bot(request)
        return jsonify(response), status_code

    app.run(host='0.0.0.0', port=8080)