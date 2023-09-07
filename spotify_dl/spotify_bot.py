import telebot
import os
import re
import logging
from dotenv import load_dotenv
import sqlite3
import datetime
import threading
import time

# Load environment variables
load_dotenv()

# Get the bot token from environment variables
bot_token = os.getenv('BOT_Spotify_TOKEN')

# Initialize the bot
bot = telebot.TeleBot(bot_token)

# SQLite Configuration
conn = sqlite3.connect('songs.db')
cursor = conn.cursor()

# Create table if it doesn't exist with an added timestamp column
cursor.execute('''
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    user_name TEXT,
    song_name TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()  # Close the initial connection

# Set up logging
logging.basicConfig(filename='telegram_bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Send me a song link!")
    logger.info(f"User {message.from_user.username} (ID: {message.from_user.id}) started the bot.")

def get_most_recently_downloaded_file():
    downloads_directory = os.path.expanduser('./downloads')
    files = [f for f in os.listdir(downloads_directory) if os.path.isfile(os.path.join(downloads_directory, f)) and f.endswith('.mp3')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(downloads_directory, x)), reverse=True)
    return os.path.join(downloads_directory, files[0]) if files else None


def extract_song_details_from_output_v2(output):
    # For a freshly downloaded song
    match = re.search(r'Downloaded "(.*?) - (.*?) - (.*?)":', output)
    if match:
        singer = match.group(1)
        song_name = match.group(2)
        additional_info = match.group(3)
        return singer, f"{singer} - {song_name} - {additional_info}.mp3"

    # For a duplicate song
    match = re.search(r'Removing duplicate file: (.*?\.mp3)', output)
    if match:
        return None, match.group(1)
    
    return None, None

# Shared variable
should_continue_sending_messages = True

# Event to signal the thread
stop_event = threading.Event()

def send_periodic_message(chat_id):
    """Send a periodic message every 5 seconds."""
    while not stop_event.is_set():
        bot.send_message(chat_id, "Please be patient, your song is being processed...")
        stop_event.wait(5)  # Wait for 5 seconds or until the event is set

@bot.message_handler(func=lambda message: True)
def handle_song_link(message):
    global should_continue_sending_messages
    # Reset the flag
    should_continue_sending_messages = True
    
    # Start the periodic message thread
    threading.Thread(target=send_periodic_message, args=(message.chat.id,)).start()
    
    # Create a new connection and cursor for this thread
    conn_local = sqlite3.connect('songs.db')
    cursor_local = conn_local.cursor()

    link = message.text
    
    # Save the current directory and switch to the 'Downloads' directory
    original_directory = os.getcwd()
    downloads_directory = os.path.expanduser('./downloads')
    if not os.path.exists(downloads_directory):
        os.makedirs(downloads_directory)
    os.chdir(downloads_directory)

    result = os.popen(f'python -m spotdl {link}').read()
    
    # Switch back to the original directory
    os.chdir(original_directory)

    singer, _ = extract_song_details_from_output_v2(result)
    song_path = get_most_recently_downloaded_file()

    if not song_path or not os.path.exists(song_path):
        bot.reply_to(message, "Sorry, couldn't find the downloaded song.")
        return

    # Send the song back to the user
    with open(song_path, 'rb') as song_file:
        bot.send_audio(message.chat.id, song_file, caption=f"Here's your song: {os.path.basename(song_path)}")

    # Log user information and the posted link
    logger.info(f"User {message.from_user.username} (ID: {message.from_user.id}) posted link: {link}")

    # Save song details to the SQLite database
    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor_local.execute("INSERT INTO songs (user_id, user_name, song_name, timestamp) VALUES (?, ?, ?, ?)", 
                (message.from_user.id, message.from_user.username, os.path.basename(song_path), current_timestamp))
    conn_local.commit()
    conn_local.close()  # Close the connection

    # Stop sending periodic messages
    stop_event.set()


bot.polling(none_stop=True)
