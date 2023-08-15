# Импорты
from config_reader import config
from reply_texts import *
from aiogram import Bot, types, Dispatcher, executor

# Объект бота
bot = Bot(token=config.bot_token.get_secret_value())
# Диспетчер
dp = Dispatcher(bot)


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, START_TEXT)


# Хэндлер на команду /help
@dp.message_handler(commands=['help'])
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, HELP_TEXT)


# Хэндлер на текстовые сообщения
@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, msg.text)


# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp)
    print("Бот запущен...")
