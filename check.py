import os
import telebot
from flask import Flask, request
from datetime import datetime

# --- Configuration (Read from Environment Variables) ---
# Render provides a standard 'PORT' environment variable.
PORT = int(os.environ.get('PORT', 5000))

# You MUST set these environment variables in Render:
# 1. BOT_TOKEN: Your Telegram bot's API token.
# 2. RENDER_URL: The base URL of your deployed service (e.g., https://my-bot-name.onrender.com)
BOT_TOKEN = ("8445866684:AAGlxIaW28IRkNmoHL8MgWdey_G2ISMlTgI")
RENDER_URL = ("https://check-d3r6.onrender.com")

# Define a secret path using the token to prevent simple abuse.
# Telegram will POST updates to: RENDER_URL/BOT_TOKEN
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = RENDER_URL + WEBHOOK_PATH

# Ch freeeck for required configuration
if not BOT_TOKEN or not RENDER_URL:
    print("CRITICAL ERROR: BOT_TOKEN or RENDER_URL environment variable is missing!")
    # Exit cleanly if environment variables are not set
    # On Render, this will cause the service to fail to start until variables are provided.
    exit(1)

# Initialize TeleBot with threaded=False
# This is crucial for compatibility with Gunicorn and shared hosting environments.
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Initialize Flask App
app = Flask(__name__)
started_at = datetime.utcnow()

# --- Webhook Setup on Startup ---
# This code runs when Gunicorn loads the application.
try:
    # 1. Remove any previously set webhooks to ensure a clean start.
    bot.remove_webhook()
    
    # 2. Set the new webhook URL for the bot API.
    # Telegram will now send updates to this URL.
    bot.set_webhook(url=WEBHOOK_URL)
    
    print(f"Webhook successfully set to: {WEBHOOK_URL}")

except Exception as e:
    # Log the failure but allow the service to start (Render health check still works)
    print(f"ERROR: Failed to set webhook! Please verify BOT_TOKEN and RENDER_URL. Details: {e}")

# --- Telegram Message Handlers ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hello! I'm alive and running via webhook on Render!")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    # Log to the console (visible in Render logs)
    print(f"Received message: {message.text} from {message.chat.id}")
    bot.reply_to(message, f"You echoed: {message.text}")

# --- Flask Routes ---

# 1. Health Check Route (Essential for Render)
@app.route("/", methods=["GET"])
def index():
    # Calculate uptime for the health check response
    uptime_seconds = (datetime.utcnow() - started_at).total_seconds()
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    uptime_str = f"{days}d {hours}h {minutes}m"
    
    return f"Bot Service Running. Uptime: {uptime_str}. Webhook Path: {WEBHOOK_PATH}", 200

# 2. Webhook Endpoint (Receives POST requests from Telegram)
@app.route(WEBHOOK_PATH, methods=["POST"])
def telegram_webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("UTF-8")
        try:
            update = telebot.types.Update.de_json(json_str)
            # Process the incoming update
            bot.process_new_updates([update])
        except Exception as e:
            # Important: Always return 200 OK to Telegram even if processing fails
            # This prevents Telegram from sending endless retries.
            print(f"Error processing update: {e}")
            return "OK (Processing Error)", 200
            
        return "OK", 200
    
    return "Invalid request (must be application/json)", 400
    
# Note: The development server start block (if __name__ == "__main__":) is removed.
# Gunicorn will be used to run 'app:app'
