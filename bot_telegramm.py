from telethon import TelegramClient, events
import re
import requests
import logging

API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
BOT_TOKEN = 'YOUR_BOT_TOKEN'
GROUP_CHAT_ID = -1001818001809

client = TelegramClient('anon', API_ID, API_HASH)
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Set up logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log the bot's start-up status
logger.info("Bot has started")

def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10

def is_luhn_valid(card_number):
    return luhn_checksum(card_number) == 0

def get_bin_info(bin_number):
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"BIN lookup for {bin_number} failed with status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"BIN lookup for {bin_number} failed with exception: {e}")
        return None

@client.on(events.NewMessage(chats=GROUP_CHAT_ID))
async def check_card(event):
    logger.info(f"Received message in chat {event.chat_id}: {event.text}")
    # Adjusted regex to account for multiline messages
    match = re.search(r'Номер карты:\s*(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})', event.text, re.MULTILINE)
    if match:
        card_number = match.group(1).replace(" ", "")
        logger.info(f"Card number found: {card_number}")
        if is_luhn_valid(card_number):
            bin_number = card_number[:6]
            bin_info = get_bin_info(bin_number)
            if bin_info:
                response_message = f"Карта валидна.\nBIN информация: {bin_info}"
            else:
                response_message = "Карта валидна, но информация о BIN не найдена."
        else:
            response_message = "Номер карты не прошел проверку по алгоритму Луна."
        await bot.send_message(event.chat_id, response_message)
        logger.info(f"Card number {card_number} checked and response sent.")

with client:
    client.run_until_disconnected()