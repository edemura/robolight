import logging
import sys

import telegram
from telegram import Bot

from dtb.settings import TELEGRAM_TOKEN


bot = Bot(TELEGRAM_TOKEN)
# Note: get_me() is now async in v20, so we'll get the username when needed
TELEGRAM_BOT_USERNAME = None
# Global variable - the best way I found to init Telegram bot
try:
    pass
except telegram.error.Unauthorized:
    logging.error("Invalid TELEGRAM_TOKEN.")
    sys.exit(1)
