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

# Ryjgrb vty. ,jnf
buttons = [
            'Расписание и направления',
            'Запись на активности',
            'Ваши мероприятия',
            'Связь с организаторами'
            ]


# Состояния бота
class BotStates(StatesGroup):
    START_STATE = State()
    HOME_STATE = State()
    ACQUAINTANCE_STATE = State()
    CHOICE_FORUM_DATE_STATE = State()


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    # Берём список всех зарегистрированных пользователей с выборков по ID
    cursor.execute(
        f''' SELECT * FROM UsersInfo WHERE tg_id={msg.from_user.id}''')
    users = cursor.fetchall()

    state = dp.current_state(user=msg.from_user.id)

    if users:
        # Формируем клавиатуру с меню по боту
        keyboard = ReplyKeyboardMarkup()
        for bnt in buttons:
            keyboard.add(KeyboardButton(bnt))

        # Отправляем ее вместе с приветственным сообщением
        # для зарегистрированного пользователя
        await bot.send_message(
            msg.from_user.id, f"Здравствуйте, {users[0][1]}!",
            reply_markup=keyboard)

        await state.set_state(BotStates.HOME_STATE.state)

    else:
        # Отправляем текст с предложением ввести ФИО
        await bot.send_message(
            msg.from_user.id,
            START_TEXT,
            parse_mode=ParseMode.MARKDOWN)

        # Переходим на стадию ввода ФИО
        await bot.send_message(msg.from_user.id, ACQUAINTANCE_TEXT)
        await state.set_state(BotStates.ACQUAINTANCE_STATE.state)


# Хэндлер на команду /help
@dp.message_handler(commands=['help'])
async def help(msg: types.Message):
    await bot.send_message(msg.from_user.id, HELP_TEXT)


# Хэндлер на текстовые сообщения
@dp.message_handler(state=BotStates.HOME_STATE)
async def reply_to_text_msg(msg: types.Message):
    if msg.text == buttons[0]:
        # Берём даты, на которые назначены мероприятия
        cursor.execute(f''' SELECT date FROM Events''')
        dates = set([i[0] for i in cursor.fetchall()])

        # Выводим их на клавиатуру
        keyboard = ReplyKeyboardMarkup()
        for date in dates:
            keyboard.add(KeyboardButton(date))

        await bot.send_message(
            msg.from_user.id,
            "Выберите дату",
            reply_markup=keyboard)

        # Переходим на выбор даты мерприятия
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.CHOICE_FORUM_DATE_STATE.state)
    elif msg.text == buttons[1]:
        pass
    elif msg.text == buttons[2]:
        pass
    elif msg.text == buttons[3]:
        # Берем список организаторов
        cursor.execute(f''' SELECT * FROM OrganizersInfo''')
        orgaizers = cursor.fetchall()

        # Формируем сообщение
        send_text = "Организаторы:"
        for org in orgaizers:
            send_text += f"\n✅ {org[0]}\n" + \
                    f"Телефон: {org[1]}\n" + \
                    f"Telegram: {org[2]}\n"

    # Отправляем
        await bot.send_message(msg.from_user.id, send_text)
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

    # Возвращаемся в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)


@dp.message_handler(state=BotStates.CHOICE_FORUM_DATE_STATE)
async def acquaintance_for_user(msg: types.Message):
    # Берем все мероприятия за введённую дату
    events = list(filter(
        lambda x: x[2] == msg.text,
        cursor.execute(f''' SELECT * FROM Events''').fetchall()))

    send_text = f"Программа форума на {msg.text}:"
    for event in events:
        # Получаем оценки мероприятия
        scores = list(map(int, event[7].split(';')[:-1]))
        # Получаем рэйтинг мероприятия
        rating = round(sum(scores) / len(scores), 1)

        send_text += f"\n✅ {event[0]}\n" + \
            f"Описание: {event[1]}\n" + \
            f"Время: {event[3]} - {event[4]}\n" + \
            f"Место: {event[5]}\n" + \
            f"Рэйтинг: {rating}/5.0\n"

    # Отправляем программу форума на выбранный день
    await bot.send_message(msg.from_user.id, send_text)

    # Выходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp)
