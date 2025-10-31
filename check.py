import telebot
from flask import Flask, request
from datetime import datetime

# Replace with your bot token
BOT_TOKEN = "8445866684:AAGlxIaW28IRkNmoHL8MgWdey_G2ISMlTgI"
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
started_at = datetime.utcnow()

# --- Telegram Message Handler ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hello! I'm alive and running on Render!")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, f"You said: {message.text}")

# --- Webhook & Health Route ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        up = (datetime.utcnow() - started_at).seconds
        return f"Bot running for {up} seconds ✅"

    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    return "Invalid request", 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)