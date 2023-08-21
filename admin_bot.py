# Импорты
from notifiers import get_notifier
from res.config_reader import config
from res.reply_texts import *

from aiogram import Bot, types, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

import sqlite3
import json

TOKEN = config.bot_token.get_secret_value()
ADMIN_TOKEN = config.admin_bot_token.get_secret_value()


# Состояния бота
class BotStates(StatesGroup):
    START_STATE = State()
    HOME_STATE = State()

    SEND_MESSAGE_STATE = State()

    CHOICE_EVENT_STATE = State()
    UPLOAD_PARTICIPANTS_LIST_STATE = State()

    CHOICE_QUEST_ACTION_STATE = State()


# Объект бота
bot = Bot(token=ADMIN_TOKEN)
# Диспетчер
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Подгружаем БД
conn = sqlite3.connect('res/data/PoleOfKnowledge_db.db')
cursor = conn.cursor()

buttons = [
    'Отправить сообщение участникам форума',
    'Выгрузить список участников мероприятия',
    'Список команд для квеста'
]


def send_notify(token: str, msg: str, chatId: int):
    telegram = get_notifier('telegram')
    telegram.notify(
        token=token,
        chat_id=chatId,
        message=msg)


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    # Формируем клавиатуру с меню по боту
    keyboard = ReplyKeyboardMarkup()
    for bnt in buttons:
        keyboard.add(KeyboardButton(bnt))
    await bot.send_message(msg.from_user.id,
                           "Выберите действие:",
                           reply_markup=keyboard)

    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.HOME_STATE.state)


# Состояние главного меню
@dp.message_handler(state=BotStates.HOME_STATE)
async def home(msg: types.Message):
    if msg.text == buttons[0]:
        keyboard = ReplyKeyboardMarkup().add(KeyboardButton("В главное меню"))
        await bot.send_message(msg.from_user.id, "Введите сообщение:",
                               reply_markup=keyboard)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.SEND_MESSAGE_STATE.state)
    elif msg.text == buttons[1]:
        events_titles_list = \
            list(map(lambda x: x[0],
                     cursor.execute(f''' SELECT title FROM Events''')
                     .fetchall()))

        # Формируем клавиатуру
        keyboard = ReplyKeyboardMarkup()
        for bnt in events_titles_list:
            keyboard.add(KeyboardButton(bnt))
        keyboard.add(KeyboardButton("В главное меню"))

        await bot.send_message(msg.from_user.id, "Выберите мероприятие:",
                               reply_markup=keyboard)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.CHOICE_EVENT_STATE.state)
    elif msg.text == buttons[2]:
        # Открываем JSON с информацией о командах для квеста
        with open('./res/data/quest_commands.json',
                  'r', encoding='utf-8') as quest_commands:
            # Читаем файл
            data = json.load(quest_commands)

        if not data:
            await bot\
                .send_message(msg.from_user.id,
                              "Участники форума не распределены на команды!")
        else:
            send_message = ""
            for team in data:
                # ФИО участников мерпориятия по ID: [ФИО1, ФИО2...]
                ids_str = ','.join(list(map(str, data[team])))
                teamers_list = \
                    [x[0] for x in cursor
                     .execute(f''' SELECT name FROM UsersInfo
                              WHERE tg_id in ({ids_str})''').fetchall()]

                # Формируем сообщение
                send_message += f"\n\n{team} ({len(teamers_list)} человек):"
                for user in teamers_list:
                    send_message += f"\n- {user}"

            # Отправляем сообщение
            await bot.send_message(msg.from_user.id, send_message)


# Отправка сообщений участникам форума от лица "клиентского" бота
@dp.message_handler(state=BotStates.SEND_MESSAGE_STATE)
async def send_msg_to_users(msg: types.Message):
    if msg.text != "В главное меню":
        # Аккаунты-администраторы
        ADMINS_ID = [i[0] for i in
                     cursor.execute(f''' SELECT * FROM Admins''').fetchall()]

        # Если пользователь админ-бота имеет нужные права
        if msg.from_user.id in ADMINS_ID:
            # Список ID зарегистрированных пользователей
            cursor.execute(
                f''' SELECT * FROM UsersInfo''')
            users = cursor.fetchall()

            await bot.send_message(msg.from_user.id, "Отправка...")

            # Перебираем ID зарегистрированных пользоателей
            for user in users:
                # Отправляем сообщение пользователю
                send_notify(token=TOKEN, msg=msg.text, chatId=user[0])

            await bot.send_message(msg.from_user.id, "Сообщение отправлено!")
        # И если нет
        else:
            # Отправляем сообщение об ошибке
            await bot.send_message(msg.from_user.id,
                                   ADMINISTRATOR_ACCESS_ERROR)

    # Выходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.HOME_STATE.state)
    await start(msg)


@dp.message_handler(state=BotStates.CHOICE_EVENT_STATE)
async def get_parts_by_event_title(msg: types.Message):
    if msg.text != "В главное меню":
        # Читаем JSON-файл с участниками мероприятий
        with open('./res/data/participants_of_events.json',
                  'r', encoding='utf-8') as participants_of_events:
            # Читаем файл
            data = json.load(participants_of_events)

        if msg.text in data:
            # Список ID участников мероприятия
            participants = data[msg.text]
            # ФИО участников мерпориятия по ID: [ФИО1, ФИО2...]
            usernames = [x[0] for x in cursor.execute(
                f''' SELECT name FROM UsersInfo
                WHERE tg_id in ({','.join(list(map(str, participants)))})'''
                ).fetchall()]

            # Формируем сообщение
            send_text = f"Участники мероприятия \"{msg.text}\" " + \
                f"({len(usernames)} человек):"
            for user in usernames:
                send_text += f"\n- {user}"

            # Отправляем сообщение
            await bot.send_message(msg.from_user.id, send_text)
        else:
            await bot.send_message(msg.from_user.id,
                                   f"На мероприятие \"{msg.text}\" еще никто" +
                                   " не зарегистрировался!")

    # Выходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.HOME_STATE.state)
    await start(msg)


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp)
