from bot import bot
from network_control import network_control
from browser_control import browser_control
from telegram_interaction import telegram_worker


bot = bot(network_control=network_control, browser_control=browser_control, telegram_worker=telegram_worker)
bot.run()