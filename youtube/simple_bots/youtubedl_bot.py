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

session = requests.Session()
session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

L = instaloader.Instaloader()
L.context._session = session
# # Initialize the instaloader instance
# L = instaloader.Instaloader(session=session)
# # time.sleep(10)  # sleep for 5 seconds
# # # Login to Instagram
L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

# Define the welcome message to be sent when the bot starts
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Log user's details
    logger.info(f"User Info - ID: {message.from_user.id}, Username: {message.from_user.username}, First Name: {message.from_user.first_name}, Last Name: {message.from_user.last_name}, Chat ID: {message.chat.id} started the bot.")
    bot.reply_to(message, "Hello! Welcome to the Downloader bot. Send a YouTube or Instagram URL to download videos.")

# Define the function to download videos
@bot.message_handler(func=lambda message: True)
def download_video(message):
    # Log the message details from the user
    logger.info(f"Received message from User - ID: {message.from_user.id}, Username: {message.from_user.username}, First Name: {message.from_user.first_name}, Last Name: {message.from_user.last_name}, Chat ID: {message.chat.id}, Text: {message.text}")

    # Check if the message contains a YouTube link
    youtube_match = re.search(YOUTUBE_URL_PATTERN, message.text)
    # Check if the message contains an Instagram link
    instagram_match = re.search(INSTAGRAM_URL_PATTERN, message.text)

    if youtube_match:
        url = youtube_match.group()
        bot.reply_to(message, "Please wait while we download the video...")

        try:
            # Use pytube to download the YouTube video
            video = pytube.YouTube(url)
            stream = video.streams.get_highest_resolution()
            filename = video.title.replace(" ", "_").replace("/", "_") + ".mp4"
            filepath = os.path.join(download_dir, filename)
            stream.download(output_path=download_dir, filename=filename)
            # Send the downloaded video back to the user
            bot.send_video(message.chat.id, open(filepath, 'rb'), timeout=10000)
        except Exception as e:
            # Log and inform the user of any errors during the YouTube download process
            logger.error(f"Error occurred for User {message.from_user.username}: {e}")
            bot.reply_to(message, f"Error: {e}")

    elif instagram_match:
        post_url = instagram_match.group()
        
        # Check if it's a story link
        if "/stories/" in post_url:
            # Extract user's username from the URL
            username = re.search(r"instagram\.com/stories/([^/]+)/", post_url).group(1)
            profile = instaloader.Profile.from_username(L.context, username)
            stories = L.get_stories(userids=[profile.userid])
            
            # Check if the profile has visible stories
            # if profile._has_public_story:
            #     stories = profile.get_stories()
            for story in stories:
                for item in story.get_items():
                    # For simplicity, let's handle just video stories
                    if item.is_video:
                        filename = f"{profile.username}_story_{item.date_local}.mp4"
                        filepath = os.path.join(os.path.abspath(download_dir), filename)
                        
                        video_url = item.video_url
                        response = requests.get(video_url, stream=True)
                        with open(filepath, 'wb') as video_file:
                            for chunk in response.iter_content(chunk_size=8192):
                                video_file.write(chunk)
                        
                        bot.send_video(message.chat.id, open(filepath, 'rb'), timeout=10000)
                        return  # Send only the first video story for simplicity
        else:
            bot.reply_to(message, "No viewable stories found for the provided username.")
            return

        # Extract the shortcode from the Instagram URL for posts/reels
        shortcode = re.search(r"instagram.com/(?:p|reel)/([^/]+)", post_url).group(1)
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            # Generate filename for the Instagram video
            filename = post.owner_username + "_" + post.shortcode + ".mp4"
            filepath = os.path.join(os.path.abspath(download_dir), filename)
            
            # Download the video using requests
            video_url = post.video_url
            response = requests.get(video_url, stream=True)
            with open(filepath, 'wb') as video_file:
                for chunk in response.iter_content(chunk_size=8192):
                    video_file.write(chunk)
            
            # Send the downloaded video back to the user
            bot.send_video(message.chat.id, open(filepath, 'rb'), timeout=10000)
        else:
            bot.reply_to(message, "The provided Instagram URL does not contain a video.")



print("About to start bot polling...")

# Start the bot and keep it running
bot.polling(timeout=1000)