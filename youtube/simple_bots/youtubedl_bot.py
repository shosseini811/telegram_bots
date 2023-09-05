# Import necessary libraries
import os
import telebot
import pytube
import re
import logging
import instaloader
from dotenv import load_dotenv
import time
import requests

# Configure logging to capture both console output and write to a file
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get the bot token and Instagram credentials from environment variables
bot_token = os.getenv('BOT_TOKEN')
# INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
# INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

# Define the directory where videos will be saved
download_dir = './downloads'

# Initialize the Telegram bot
bot = telebot.TeleBot(bot_token)

# Define regex patterns to match YouTube and Instagram URLs
YOUTUBE_URL_PATTERN = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
INSTAGRAM_URL_PATTERN = r'https://www.instagram.com/(p|reel)/[A-Za-z0-9_-]+/'

session = requests.Session()
session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

L = instaloader.Instaloader()
L.context._session = session
# # Initialize the instaloader instance
# L = instaloader.Instaloader(session=session)
# # time.sleep(10)  # sleep for 5 seconds
# # # Login to Instagram
# # L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)



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
        try:
            # Extract the shortcode from the Instagram URL
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
        except Exception as e:
            # Log and inform the user of any errors during the Instagram download process
            logger.error(f"Error occurred for User {message.from_user.username} when downloading from Instagram: {e}")
            bot.reply_to(message, f"Error: {e}")

    else:
        bot.reply_to(message, "No valid YouTube or Instagram URL found. Please provide a valid URL.")

# Start the bot and keep it running
bot.polling(timeout=1000)
