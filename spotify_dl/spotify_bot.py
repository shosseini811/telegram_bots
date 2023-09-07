import telebot
import os
import re
import boto3
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the bot token from environment variables
bot_token = os.getenv('BOT_Spotify_TOKEN')

# Initialize the bot
bot = telebot.TeleBot(bot_token)

# AWS S3 Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
s3 = boto3.client('s3')

# Set up logging
logging.basicConfig(filename='telegram_bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Send me a song link!")
    logger.info(f"User {message.from_user.username} (ID: {message.from_user.id}) started the bot.")

def get_most_recently_downloaded_file():
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.mp3')]
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files[0] if files else None

def extract_song_details_from_output(output):
    # Extract singer and song name
    match = re.search(r'Skipping (.*?) - (.*?) \(file already exists\)', output)
    if match:
        singer = match.group(1)
        song_name = match.group(2).replace(' ', '_') + '.mp3'
        return singer, song_name
    return None, None

@bot.message_handler(func=lambda message: True)
def handle_song_link(message):
    link = message.text
    result = os.popen(f'python -m spotdl {link}').read()
    singer, song_path = extract_song_details_from_output(result)
    if not singer or not song_path:
        song_path = get_most_recently_downloaded_file()
    else:
        # Create directory based on singer's name
        if not os.path.exists(singer):
            os.makedirs(singer)
        song_path = os.path.join(singer, song_path)

    if not song_path or not os.path.exists(song_path):
        bot.reply_to(message, "Sorry, couldn't find the downloaded song.")
        return

    # Upload the song to AWS S3
    s3.upload_file(song_path, S3_BUCKET_NAME, song_path)

    # Notify user of the upload
    bot.reply_to(message, f"Song uploaded to S3: {song_path}")

    # Send the song back to the user
    with open(song_path, 'rb') as song_file:
        bot.send_audio(message.chat.id, song_file, caption=f"Here's your song: {song_path}")

    # Log user information and the posted link
    logger.info(f"User {message.from_user.username} (ID: {message.from_user.id}) posted link: {link}")

bot.polling(none_stop=True)
