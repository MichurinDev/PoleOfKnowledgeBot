# Импорты
from res.config_reader import config
from res.reply_texts import *

from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ParseMode, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import sqlite3
import json

# Объект бота
bot = Bot(token=config.bot_token.get_secret_value())
# Диспетчер
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Подгружаем БД
conn = sqlite3.connect('res/data/PoleOfKnowledge_db.db')
cursor = conn.cursor()

# Временная переменная для передачи данных между чем-лиюл
_temp = None

# Ryjgrb vty. ,jnf
buttons = [
            'Расписание и направления',
            'Запись на активности',
            'Ваши мероприятия',
            'Оставить отзыв',
            'Связь с организаторами'
            ]


# Состояния бота
class BotStates(StatesGroup):
    START_STATE = State()
    HOME_STATE = State()
    ACQUAINTANCE_STATE = State()

    CHOICE_FORUM_DATE_STATE = State()

    CHOICE_FORUM_DATE_FOR_EVAL_STATE = State()
    CHOICE_EVENT_STATE = State()
    EVAL_EVENT_STATE = State()

    CHOICE_FORUM_DATE_FOR_SING_UP_FOR_EVENT = State()
    CHOICE_EVENT_SING_UP_FOR_EVENT = State()


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
            "Выберите дату:",
            reply_markup=keyboard)

        # Переходим на выбора даты мерприятия
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.CHOICE_FORUM_DATE_STATE.state)
    elif msg.text == buttons[1]:
        # Берём даты, на которые назначены мероприятия
        cursor.execute(f''' SELECT date FROM Events''')
        dates = set([i[0] for i in cursor.fetchall()])

        # Формируем клавиатуру
        keyboard = ReplyKeyboardMarkup()
        for date in dates:
            keyboard.add(KeyboardButton(date))

        # Добавляем гнопку выхода в главное меню
        keyboard.add(KeyboardButton("В главное меню"))

        await bot.send_message(
            msg.from_user.id,
            "Выберите дату:",
            reply_markup=keyboard)

        # Переходим на выбора даты мерприятия
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(
            BotStates.CHOICE_FORUM_DATE_FOR_SING_UP_FOR_EVENT.state)
    elif msg.text == buttons[2]:
        pass
    elif msg.text == buttons[3]:
        # Берём даты, на которые назначены мероприятия
        cursor.execute(f''' SELECT date FROM Events''')
        dates = set([i[0] for i in cursor.fetchall()])

        # Формируем клавиатуру
        keyboard = ReplyKeyboardMarkup()
        for date in dates:
            keyboard.add(KeyboardButton(date))

        await bot.send_message(
            msg.from_user.id,
            "Выберите дату:",
            reply_markup=keyboard)

        # Переходим на выбора даты мерприятия
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.CHOICE_FORUM_DATE_FOR_EVAL_STATE.state)
    elif msg.text == buttons[4]:
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
async def send_events_list(msg: types.Message):
    # Берем все мероприятия за введённую дату
    events = list(filter(
        lambda x: x[2] == msg.text,
        cursor.execute(f''' SELECT * FROM Events''').fetchall()))

    send_text = f"Программа форума на {msg.text}:"
    for event in events:
        # Получаем оценки мероприятия
        scores = list(map(int, event[7].split(';')[:-1]))
        # Получаем рейтинг мероприятия
        rating = round(sum(scores) / len(scores), 1)

        send_text += f"\n✅ {event[0]}\n" + \
            f"Описание: {event[1]}\n" + \
            f"Время: {event[3]} - {event[4]}\n" + \
            f"Место: {event[5]}\n" + \
            f"Рейтинг: {rating}/5.0\n"

    # Отправляем программу форума на выбранный день
    await bot.send_message(msg.from_user.id, send_text)

    # Выходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)


@dp.message_handler(state=BotStates.CHOICE_FORUM_DATE_FOR_EVAL_STATE)
async def choice_event_data(msg: types.Message):
    # Берем все мероприятия за введённую дату
    events = list(filter(
        lambda x: x[2] == msg.text,
        cursor.execute(f''' SELECT * FROM Events''').fetchall()))

    send_text = f"Выберите мероприятие:\n"
    keyboard = ReplyKeyboardMarkup()

    for event in events:
        # Добавляем название в список мероприятий
        send_text += f"{event[0]}\n"
        # Формируем клавиатуру со списком мероприятий
        keyboard.add(KeyboardButton(event[0]))

    # Отправляем список мероприятий на выбранный день
    await bot.send_message(msg.from_user.id, send_text, reply_markup=keyboard)

    # Переходим на этап выбора мероприятия
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.CHOICE_EVENT_STATE)


@dp.message_handler(state=BotStates.CHOICE_EVENT_STATE)
async def choice_event(msg: types.Message):
    global _temp

    # Берем список оценок
    event = list(filter(
        lambda x: x[0] == msg.text,
        cursor.execute(f''' SELECT * FROM Events''').fetchall()))[0]

    # Берем оценки мероприятия
    event_scores = event[7]
    _temp = [event[0], event_scores]

    keyboard = ReplyKeyboardMarkup()
    for i in range(1, 6):
        keyboard.add(KeyboardButton(str(i)))

    await bot.send_message(
        msg.from_user.id,
        "Поставьте оценку мероприятию по шкале от 1 до 5:",
        reply_markup=keyboard)

    # Переходим на этап оценивания
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.EVAL_EVENT_STATE)


@dp.message_handler(state=BotStates.EVAL_EVENT_STATE)
async def score_event(msg: types.Message):
    global _temp
    if msg.text in "12345":
        # Добавляем оценку
        _temp[1] += f'{msg.text};'

        # Обновляем оценки мероприятия
        cursor.execute(f'''UPDATE Events SET scores = ? WHERE title = ?''',
                       (_temp[1], _temp[0]))
        conn.commit()

        await bot.send_message(
            msg.from_user.id,
            f"Оценка \"{msg.text}\" мероприятию \"{_temp[0]}\" поставлена!")

        # "Обнуляем" временную переменную
        _temp = None

        # Переходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)
    else:
        # Отправляем сообщение об ошибке
        bot.send_message(msg.from_user.id, "Неверное значение!")

        # Еще раз просим ввести число
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.CHOICE_EVENT_STATE)
        await choice_event(msg)


@dp.message_handler(state=BotStates.CHOICE_FORUM_DATE_FOR_SING_UP_FOR_EVENT)
async def score_event(msg: types.Message):
    if msg.text == "В главное меню":
        # Переходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)
    else:
        # Берем все мероприятия за введённую дату
        events = list(filter(
            lambda x: x[8] > x[9] and x[2] == msg.text,
            cursor.execute(f''' SELECT * FROM Events''').fetchall()))

        send_text = "Выберите мероприятие:\n"
        keyboard = ReplyKeyboardMarkup()

        # Читаем JSON-файл с участниками мероприятий
        with open('./res/data/participants_of_events.json',
                  'r', encoding='utf-8') as participants_of_events:
            # Читаем файл
            data = json.load(participants_of_events)

        for event in events:
            # Если мероприятие есть в JSON-файле и
            # на него не зарегистрирован пользователь
            # или если мероприятия нет в JSON-файле
            if (event[0] in data and
                msg.from_user.id not in data[event[0]]) or \
                    (event[0] not in data):
                # Добавляем название в список мероприятий
                send_text += f"{event[0]}\n"
                # Формируем клавиатуру со списком мероприятий
                keyboard.add(KeyboardButton(event[0]))

        if send_text != "Выберите мероприятие:\n":
            # Отправляем список мероприятий на выбранный день
            await bot.send_message(msg.from_user.id,
                                   send_text,
                                   reply_markup=keyboard)

            # Переходим на этап выбора мероприятия
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.CHOICE_EVENT_SING_UP_FOR_EVENT)
        else:
            await bot.send_message(msg.from_user.id,
                                   "На выбранный днень " +
                                   "нет доступных мероприятий",
                                   reply_markup=keyboard)


@dp.message_handler(state=BotStates.CHOICE_EVENT_SING_UP_FOR_EVENT)
async def score_event(msg: types.Message):
    # Открываем JSON со структурой Мероприятие: [участник 1, участник 2...]
    with open('./res/data/participants_of_events.json',
              'r', encoding='utf-8') as participants_of_events:
        # Читаем файл
        data = json.load(participants_of_events)

    # Добавляем участника на мероприятие,
    # если на это мероприятие уже кто-то регистрировался
    if msg.text in data:
        data[msg.text].append(msg.from_user.id)
    # И если нет
    else:
        data[msg.text] = [msg.from_user.id]

    # Обновляем JSON-файл
    with open('./res/data/participants_of_events.json',
              'w', encoding='utf-8') as participants_of_events:
        json.dump(data, participants_of_events, indent=4, ensure_ascii=False)

    # Берём текущее количество участников
    currentParticipantsCounter = \
        cursor.execute(f''' SELECT currentParticipants FROM Events
                        WHERE title = ?''', (msg.text,)).fetchall()[0][0]

    # Обновляем текущее число участников у мероприятия
    cursor.execute(f'''UPDATE Events SET currentParticipants = ?
                   WHERE title = ?''',
                   (currentParticipantsCounter + 1, msg.text))
    conn.commit()

    # Отправляем сообщение об успешной регистрации участника на мероприятие
    await bot.send_message(msg.from_user.id,
                           "Вы успешно зарегистрировались " +
                           f"на мероприятие \"{msg.text}\"")

    # Переходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp)
