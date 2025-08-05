from aiogram import Bot, Dispatcher

from data import config

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot=bot)
