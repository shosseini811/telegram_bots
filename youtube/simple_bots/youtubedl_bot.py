import os
import telebot
import pytube
import re
import logging
from dotenv import load_dotenv
import time

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
download_dir = './downloads'

bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logger.info(f"User {message.from_user.username} started the bot.")
    bot.reply_to(message, "Hello! Welcome to the YouTube Downloader bot. Just send a YouTube URL to download videos.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    youtube_url_pattern = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    url_match = re.search(youtube_url_pattern, message.text)

    if url_match:
        logger.info(f"User {message.from_user.username} provided YouTube URL: {url_match.group()}")
    else:
        logger.warning(f"User {message.from_user.username} provided invalid URL: {message.text}")
        bot.reply_to(message, "No YouTube URL found. Please provide a valid YouTube URL.")
        return

    try:
        url = url_match.group()
        video = pytube.YouTube(url)
        stream = video.streams.get_highest_resolution()
        filename = f"{video.title}.mp4"
        filepath = os.path.join(download_dir, filename)
        start_time = time.time()
        stream.download(output_path=download_dir, filename=filename)
        end_time = time.time() 
        logger.info(f"Downloaded {filename} in {end_time - start_time} seconds.")
        
        file_size = os.path.getsize(filepath) // 1024  # File size in KB
        bot.reply_to(message, f"Downloaded {filename}. File size: {file_size} KB")
        bot.send_video(message.chat.id, open(filepath, 'rb'), timeout=10000)
    except pytube.exceptions.AgeRestrictedError:
        logger.warning(f"User {message.from_user.username} tried to download an age-restricted video: {url}")
        bot.reply_to(message, "Sorry, I can't download age-restricted videos.")
    except Exception as e:
        logger.error(f"Error occurred for User {message.from_user.username}: {e}")
        bot.reply_to(message, f"Error: {e}")

bot.polling(timeout=1000)
