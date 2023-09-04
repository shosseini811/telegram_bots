import os
import telebot
import pytube
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
download_dir = './downloads'

bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Welcome to the YouTube Downloader bot. Use /download [YouTube_URL] to download videos.")

@bot.message_handler(commands=['download'])
def download_video(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Please provide a YouTube URL.")
            return

        url = parts[1]
        video = pytube.YouTube(url)
        stream = video.streams.get_highest_resolution()
        filename = f"{video.title}.mp4"
        filepath = os.path.join(download_dir, filename)
        stream.download(output_path=download_dir, filename=filename)
        
        file_size = os.path.getsize(filepath) // 1024  # File size in KB
        bot.reply_to(message, f"Downloaded {filename}. File size: {file_size} KB")

        bot.send_video(message.chat.id, open(filepath, 'rb'), timeout=10000)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

bot.polling(timeout=1000)
