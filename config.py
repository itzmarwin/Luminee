import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

# Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")

# Your API ID from my.telegram.org
APP_ID = int(os.environ.get("APP_ID", ""))

# Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "")

# Your db channel Id
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", ""))

# OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", ""))

# Port
PORT = os.environ.get("PORT", "8080")

# Database 
DB_URI = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "filesharexbot")

# Force sub channels (comma-separated list)
FORCE_SUB_CHANNELS = [int(x.strip()) for x in os.environ.get("FORCE_SUB_CHANNELS", "").split(",")] if os.environ.get("FORCE_SUB_CHANNELS") else []

# Join request method (True/False)
JOIN_REQUEST_ENABLE = os.environ.get("JOIN_REQUEST_ENABLED", "False") == "True"

# Bot workers
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

# Start message
START_PIC = os.environ.get("START_PIC", "")
START_MSG = os.environ.get("START_MESSAGE", "Hello {first}\n\nI can store private files in Specified Channel and other users can access it from special link.")

# Admins list
try:
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split()] if os.environ.get("ADMINS") else []
except ValueError:
    raise Exception("Your Admins list does not contain valid integers.")

# Force sub message 
FORCE_MSG = os.environ.get(
    "FORCE_SUB_MESSAGE", 
    "Hello {first}\n\n<b>You need to join all our channels to use this bot</b>"
)

# Custom Caption
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

# Protect content (prevent forwarding)
PROTECT_CONTENT = os.environ.get('PROTECT_CONTENT', "False") == "True"

# Auto delete settings
AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", "0"))
AUTO_DELETE_MSG = os.environ.get(
    "AUTO_DELETE_MSG", 
    "This file will be automatically deleted in {time} seconds. Please ensure you have saved any necessary content before this time."
)
AUTO_DEL_SUCCESS_MSG = os.environ.get(
    "AUTO_DEL_SUCCESS_MSG", 
    "Your file has been successfully deleted. Thank you for using our service. ✅"
)

# Disable channel button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False") == 'True'

# Bot stats text
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"

# User reply text
USER_REPLY_TEXT = "❌ Don't send me messages directly! I'm only a File Share bot."

# Add owner to admins
ADMINS.append(OWNER_ID)

# Logging configuration
LOG_FILE_NAME = "filesharingbot.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50_000_000,  # 50 MB
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
