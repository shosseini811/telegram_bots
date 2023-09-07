import telebot
import os
import re
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

# Get the bot token and Instagram credentials from environment variables
bot_token = os.getenv('BOT_Spotify_TOKEN')

# Initialize the bot
bot = telebot.TeleBot(bot_token)

# Command to start the bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Send me a song link!")


def get_most_recently_downloaded_file():
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.mp3')]
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    if files:
        return files[0]  # Return the most recently downloaded .mp3 file
    return None

# Extract song name from SpotDL output
def extract_song_name_from_output(output):
    # Regular expression to match the song pattern in SpotDL's output
    match = re.search(r'Skipping (.*?) \(file already exists\)', output)
    if match:
        return match.group(1).replace(' ', '_') + '.mp3'
    return None

# Handle song links sent by users
@bot.message_handler(func=lambda message: True)
def handle_song_link(message):
    link = message.text
    
    # Use SpotDL to download the song and capture its output
    result = os.popen(f'python -m spotdl {link}').read()
    
    # If the song was a duplicate, extract its name from the output
    if "file already exists" in result:
        song_path = extract_song_name_from_output(result)
    else:
        # Get the most recently downloaded song
        song_path = get_most_recently_downloaded_file()

    # If we couldn't find a song, send an error message
    if not song_path or not os.path.exists(song_path):
        bot.reply_to(message, "Sorry, couldn't find the downloaded song.")
        return

    # Send the song back to the user
    with open(song_path, 'rb') as song_file:
        bot.send_audio(message.chat.id, song_file)


# Polling loop to keep the bot running
bot.polling(none_stop=True)
