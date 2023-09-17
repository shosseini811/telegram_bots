# Import necessary libraries
import telebot
import pytube
import re
import logging
import instaloader
import os
from os.path import join, dirname
from dotenv import load_dotenv
import time
import requests

# Your existing logging setup
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Set telebot's log level to DEBUG
telebot_logger = logging.getLogger('telebot')
telebot_logger.setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

# Define the directory where videos will be saved
download_dir = './downloads'

# Initialize the Telegram bot
bot = telebot.TeleBot(bot_token)

# Define regex patterns to match YouTube and Instagram URLs
YOUTUBE_URL_PATTERN = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
INSTAGRAM_URL_PATTERN = r'https://(www\.)?instagram\.com/(p|reel|stories)/[A-Za-z0-9_-]+/?(\?[^ ]+)?'

L = instaloader.Instaloader()
SESSION_FILE = "session-soheilhosseini82"
L.load_session_from_file(INSTAGRAM_USERNAME, SESSION_FILE)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logger.info(f"User Info - ID: {message.from_user.id}, Username: {message.from_user.username}, First Name: {message.from_user.first_name}, Last Name: {message.from_user.last_name}, Chat ID: {message.chat.id} started the bot.")
    bot.reply_to(message, "Hello! Welcome to the Downloader bot. Send a YouTube or Instagram URL to download videos.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    logger.info(f"Received message from User - ID: {message.from_user.id}, Username: {message.from_user.username}, First Name: {message.from_user.first_name}, Last Name: {message.from_user.last_name}, Chat ID: {message.chat.id}, Text: {message.text}")

    youtube_match = re.search(YOUTUBE_URL_PATTERN, message.text)
    instagram_match = re.search(INSTAGRAM_URL_PATTERN, message.text)

    if youtube_match:
        url = youtube_match.group()
        bot.reply_to(message, "Please wait while we download the video...")
        try:
            video = pytube.YouTube(url)
            stream = video.streams.get_highest_resolution()
            filename = video.title.replace(" ", "_").replace("/", "_") + ".mp4"
            filepath = os.path.join(download_dir, filename)
            stream.download(output_path=download_dir, filename=filename)
            bot.send_video(message.chat.id, open(filepath, 'rb'), timeout=10000)
        except Exception as e:
            logger.error(f"Error occurred for User {message.from_user.username}: {e}")
            bot.reply_to(message, f"Error: {e}")

    elif instagram_match:
        post_url = instagram_match.group()
        if "/stories/" in post_url:
            bot.reply_to(message, "Downloading Stories is not supported yet.")

            # match = re.search(r"instagram\.com/stories/([^/]+)/([^/?]+)", message.text)
            # if match:
            #     username = match.groups()[0]
            #     story_id = match.groups()[1]
            #     profile = instaloader.Profile.from_username(L.context, username)
            #     stories = L.get_stories(userids=[profile.userid])
            #     for story in stories:
            #         for item in story.get_items():
            #             if str(item.mediaid) == story_id:
            #                 if item.is_video:
            #                     filename = f"{profile.username}_story_{item.date_local}.mp4"
            #                     filepath = os.path.join(os.path.abspath(download_dir), filename)
            #                     video_url = item.video_url
            #                     response = requests.get(video_url, stream=True)
            #                     with open(filepath, 'wb') as video_file:
            #                         for chunk in response.iter_content(chunk_size=8192):
            #                             video_file.write(chunk)
            #                     bot.send_video(message.chat.id, open(filepath, 'rb'), timeout=10000)
            #                     return

        else:
            shortcode_match = re.search(r"instagram.com/(?:p|reel)/([^/]+)", post_url)
            if shortcode_match:
                shortcode = shortcode_match.group(1)
                try:
                    post = instaloader.Post.from_shortcode(L.context, shortcode)
                except Exception as e:
                    logger.error(f"JSON Query to api/v1/media/{shortcode}/info/: HTTP error code 403. [retrying; skip with ^C]")
                    logger.error(f"Unable to fetch high-quality video version of <Post {shortcode}>: {e}")
                    return
                
                if post.is_video:
                    filename = f"{post.owner_username}_{post.date_local}.mp4"
                    filepath = os.path.join(os.path.abspath(download_dir), filename)
                    video_url = post.video_url
                    response = requests.get(video_url, stream=True)
                    with open(filepath, 'wb') as video_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            video_file.write(chunk)
                    bot.send_video(message.chat.id, open(filepath, 'rb'), timeout=10000)
                else:
                    bot.reply_to(message, "The provided Instagram URL does not contain a video.")
            else:
                bot.reply_to(message, "Invalid post/reel link provided.")
                return
    else:
        bot.reply_to(message, "Invalid URL. Please send a valid YouTube or Instagram URL.")

logger.info("About to start bot polling...")
bot.polling(timeout=1000)
