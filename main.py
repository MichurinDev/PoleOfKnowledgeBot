# Импорты
from res.config_reader import config
from res.reply_texts import *

from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ParseMode, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import sqlite3

# Объект бота
bot = Bot(token=config.bot_token.get_secret_value())
# Диспетчер
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Подгружаем БД
conn = sqlite3.connect('res/db/PoleOfKnowledge_db.db')
cursor = conn.cursor()


# Состояния бота
class BotStates(StatesGroup):
    START_STATE = State()
    HOME_STATE = State()
    ACQUAINTANCE_STATE = State()


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    cursor.execute(
        f''' SELECT * FROM UsersInfo WHERE tg_id={msg.from_user.id}''')
    users = cursor.fetchall()

    state = dp.current_state(user=msg.from_user.id)

    if users:
        buttons = [
            'Расписание и направления',
            'Запись на активности',
            'Ваши мероприятия',
            'Связь с организаторами'
            ]

        greet_kb = ReplyKeyboardMarkup()
        for bnt in buttons:
            greet_kb.add(KeyboardButton(bnt))

        await bot.send_message(
            msg.from_user.id, f"Здравствуйте, {users[0][1]}!",
            reply_markup=greet_kb)

        await state.set_state(BotStates.HOME_STATE.state)

    else:
        await bot.send_message(
            msg.from_user.id,
            START_TEXT,
            parse_mode=ParseMode.MARKDOWN)

        await bot.send_message(msg.from_user.id, ACQUAINTANCE_TEXT)
        await state.set_state(BotStates.ACQUAINTANCE_STATE.state)


# Хэндлер на команду /help
@dp.message_handler(commands=['help'])
async def help(msg: types.Message):
    await bot.send_message(msg.from_user.id, HELP_TEXT)


# Хэндлер на текстовые сообщения
@dp.message_handler(state=BotStates.HOME_STATE)
async def reply_to_text_msg(msg: types.Message):
    if msg.text == "Связь с организаторами":
        cursor.execute(f''' SELECT * FROM OrganizersInfo''')
        orgaizers = cursor.fetchall()

        text = "Организаторы:"
        for org in orgaizers:
            text += f'\n✅{org[0]}\nТелефон: {org[1]}\nTelegram: {org[2]}\n'

        await bot.send_message(msg.from_user.id, text)
    elif msg.text == "/start":
        await start(msg)
    elif msg.text == "/help":
        await help(msg)


@dp.message_handler(state=BotStates.ACQUAINTANCE_STATE)
async def acquaintance_for_user(msg: types.Message):
    # Добавляем нового пользователя
    cursor.execute('INSERT INTO UsersInfo (tg_id, name) VALUES (?, ?)',
                   (msg.from_user.id, msg.text))
    conn.commit()

    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp)
