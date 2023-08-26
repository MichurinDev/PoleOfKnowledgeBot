# Импорты
from res.config_reader import config
from res.reply_texts import *
from res.SendNotify import send_notify

from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ParseMode, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import sqlite3
import json
from random import choice

# Объект бота
TOKEN = config.bot_token.get_secret_value()
bot = Bot(token=TOKEN)
# Диспетчер
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Подгружаем БД
conn = sqlite3.connect('res/data/PoleOfKnowledge_db.db')
cursor = conn.cursor()

# Временная переменная для передачи данных между чем-либо
_temp = None
user_city = ""

# Кнопки главного меню
buttons = [
            'Показать расписание',
            'Записаться на воркшопы',
            'Твои мероприятия',
            'Награды',
            'Оценить мероприятие',
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

    CHOICE_FORUM_DATE_FOR_GET_MY_EVENTS = State()


def getValueByTgID(table="UsersInfo", value_column="id", tgID=None):
    if tgID:
        return cursor.execute(f''' SELECT {value_column} FROM
                              {table} WHERE tg_id=?''',
                              (tgID,)).fetchall()[0][0]
    else:
        print("ERROR: Telegram ID is None")


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    global user_city

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
        if msg.text == "/start":
            await bot.send_message(
                msg.from_user.id, f"Привет-привет!")

        user_city = cursor.execute('''SELECT city FROM
                                   UsersInfo WHERE tg_id=?''',
                                   (msg.from_user.id,)).fetchall()[0][0]

        await bot.send_message(msg.from_user.id,
                               MENU_TEXT, reply_markup=keyboard)
        await state.set_state(BotStates.HOME_STATE.state)

    else:
        # Отправляем текст с предложением ввести ID
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
        cursor.execute(f''' SELECT date FROM Events WHERE city=?''',
                       (user_city,))
        dates = set([i[0] for i in cursor.fetchall()])

        # Формируем клавиатуру
        keyboard = ReplyKeyboardMarkup()
        for date in dates:
            keyboard.add(KeyboardButton(date))
        keyboard.add(KeyboardButton("В главное меню"))

        # Отправляем сообщение
        await bot.send_message(
            msg.from_user.id,
            "Выбери дату:",
            reply_markup=keyboard)

        # Переходим на выбора даты мерприятия
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.CHOICE_FORUM_DATE_STATE.state)
    elif msg.text == buttons[1]:
        # Берём даты, на которые назначены мероприятия
        cursor.execute(f''' SELECT date FROM Events WHERE city=?''',
                       (user_city,))
        dates = set([i[0] for i in cursor.fetchall()])

        # Формируем клавиатуру
        keyboard = ReplyKeyboardMarkup()
        for date in dates:
            keyboard.add(KeyboardButton(date))

        # Добавляем кнопку выхода в главное меню
        keyboard.add(KeyboardButton("В главное меню"))

        # Отправляем сообщение
        await bot.send_message(
            msg.from_user.id,
            "На старт, внимание, регистрация! Скорее выбирай воркшоп, " +
            "на который ты сегодня пойдешь. " +
            "Поторопись, места разлетаются как аппетитные косточки!")
        await bot.send_message(
            msg.from_user.id,
            "Выбери дату:",
            reply_markup=keyboard)

        # Переходим на выбора даты мерприятия
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(
            BotStates.CHOICE_FORUM_DATE_FOR_SING_UP_FOR_EVENT.state)
    elif msg.text == buttons[2]:
        # Берём даты, на которые назначены мероприятия
        cursor.execute(f''' SELECT date FROM Events WHERE city=?''',
                       (user_city,))
        dates = set([i[0] for i in cursor.fetchall()])

        # Формируем клавиатуру
        keyboard = ReplyKeyboardMarkup()
        for date in dates:
            keyboard.add(KeyboardButton(date))
        keyboard.add(KeyboardButton("В главное меню"))

        # Отправляем сообщение
        await bot.send_message(
            msg.from_user.id,
            "Выбери дату:",
            reply_markup=keyboard)

        # Переходим на выбора даты мерприятия
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(
            BotStates.CHOICE_FORUM_DATE_FOR_GET_MY_EVENTS.state)
    elif msg.text == buttons[3]:
        await bot.send_message(msg.from_user.id, "Текст про награды")
    elif msg.text == buttons[4]:
        # Берём даты, на которые назначены мероприятия
        cursor.execute(f''' SELECT date FROM Events WHERE city=?''',
                       (user_city,))
        dates = set([i[0] for i in cursor.fetchall()])

        # Формируем клавиатуру
        keyboard = ReplyKeyboardMarkup()
        for date in dates:
            keyboard.add(KeyboardButton(date))
        keyboard.add(KeyboardButton("В главное меню"))

        # Отправляем сообщение
        await bot.send_message(
            msg.from_user.id,
            "Выбери дату:",
            reply_markup=keyboard)

        # Переходим на выбора даты мерприятия
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.CHOICE_FORUM_DATE_FOR_EVAL_STATE.state)
    elif msg.text == buttons[5]:
        pass
    elif msg.text == "/start":
        await start(msg)
    elif msg.text == "/help":
        await help(msg)


@dp.message_handler(state=BotStates.ACQUAINTANCE_STATE)
async def acquaintance_for_user(msg: types.Message):
    # Если пользователь с введёным ID существует
    if cursor.execute('SELECT * FROM UsersInfo WHERE id=? AND tg_id IS NULL',
                      (msg.text,)).fetchall():
        # Добавляем нового пользователя
        cursor.execute('''UPDATE UsersInfo SET tg_id=?
                       WHERE id=? AND tg_id IS NULL''',
                       (msg.from_user.id, msg.text))
        conn.commit()

        # Распределяем в команду для квеста
        # Открываем JSON с информацией о командах для квеста
        with open('./res/data/quest_commands.json',
                  'r', encoding='utf-8') as quest_commands:
            # Читаем файл
            data = json.load(quest_commands)

        # Получаем тип пользователя
        user_type = cursor.execute(
                f''' SELECT type FROM UsersInfo WHERE id=?''',
                (msg.text)).fetchall()[0][0]

        # Если пользователь - ученик
        if user_type == "Ученик":
            # Получаем название команды
            team_name = sorted(data, key=lambda s: len(data[s]))[0]
            # Добавляем туда нового пользователя
            data[team_name].append(msg.from_user.id)

            # И отправляем сообщение о распределении
            await bot.send_message(
                msg.from_user.id,
                'Кррррутяк! Я от радости даже начал вилять своим ' +
                f'электронным хвостом! Теперь ты в команде {team_name}. ' +
                'Тебе выдадут браслет с цветом твоей команды.')

            # Обновляем JSON-файл
            with open('./res/data/quest_commands.json',
                      'w', encoding='utf-8') as quest_commands:
                json.dump(data,
                          quest_commands,
                          indent=4,
                          ensure_ascii=False)

        # Возвращаемся в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)
    # А если не существует
    else:
        await bot.send_message(msg.from_user.id, ID_ERROR_TEXT)


@dp.message_handler(state=BotStates.CHOICE_FORUM_DATE_STATE)
async def send_events_list(msg: types.Message):
    if msg.text == "В главное меню":
        # Выходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)
    else:
        # Берем все мероприятия за введённую дату
        events = cursor.execute(f''' SELECT * FROM Events WHERE date=?
                                AND city=?''',
                                (msg.text, user_city)).fetchall()

        send_text = ""
        for event in events:
            send_text += f"\n✅ {event[0]}\n" + \
                f"Описание: {event[1]}\n" + \
                f"Время: {event[3]} - {event[4]}\n" + \
                f"Место: {event[5]}\n" + \
                f"Количество мест: {event[7] - event[8]}/{event[7]}\n"

        # Если мероприятия найдены
        if send_text != "":
            # Отправляем программу форума на выбранный день
            await bot.send_message(
                msg.from_user.id,
                choice(TIMETABLE_TITLE_TEXTS))
            await bot.send_message(msg.from_user.id, send_text)

            # Выходим в главное меню
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.START_STATE)
            await start(msg)
        # А если нет мероприятий в выбранную дату
        else:
            await bot.send_message(msg.from_user.id,
                                   "На выбранный день " +
                                   "нет мероприятий")


@dp.message_handler(state=BotStates.CHOICE_FORUM_DATE_FOR_EVAL_STATE)
async def choice_event_data(msg: types.Message):
    if msg.text != "В главное меню":
        # Берем все мероприятия за введённую дату
        events = cursor.execute(f''' SELECT * FROM Events WHERE date=?
                                AND city=?''',
                                (msg.text, user_city)).fetchall()

        # Если мероприятия найдены
        if events:
            send_text = f"Выбери мероприятие:\n"
            keyboard = ReplyKeyboardMarkup()

            for event in events:
                # Добавляем название в список мероприятий
                send_text += f"{event[0]}\n"
                # Формируем клавиатуру со списком мероприятий
                keyboard.add(KeyboardButton(event[0]))
            keyboard.add(KeyboardButton("В главное меню"))

            # Отправляем список мероприятий на выбранный день
            await bot.send_message(msg.from_user.id,
                                   send_text,
                                   reply_markup=keyboard)

            # Переходим на этап выбора мероприятия
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.CHOICE_EVENT_STATE)
        # И если не найдены
        else:
            await bot.send_message(msg.from_user.id,
                                   "Мероприятий в данный день нет!")
    else:
        # Выходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)


@dp.message_handler(state=BotStates.CHOICE_EVENT_STATE)
async def choice_event(msg: types.Message):
    global _temp

    if msg.text != "В главное меню":
        # Если мероприятия с таким названием есть
        if cursor.execute(f''' SELECT * FROM Events WHERE title=?
                          AND city=?''',
                          (msg.text, user_city)).fetchall():
            # Берем оценки мероприятия
            event_scores = cursor.execute(f''' SELECT scores
                                          FROM Events WHERE title=?
                                          AND city=?''',
                                          (msg.text, user_city))\
                                            .fetchall()[0][0]
            # Сохраняем название и оценки мероприятия
            _temp = [msg.text, event_scores]

            # Формируем клавиатуру
            keyboard = ReplyKeyboardMarkup()
            for i in range(1, 6):
                keyboard.add(KeyboardButton(str(i)))
            keyboard.add(KeyboardButton("В главное меню"))

            # Отправляем сообщение
            await bot.send_message(
                msg.from_user.id,
                "Поставьте оценку мероприятию по шкале от 1 до 5:",
                reply_markup=keyboard)

            # Переходим на этап оценивания
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.EVAL_EVENT_STATE)
        # И если нет
        else:
            await bot.send_message(msg.from_user.id, "Мероприятие на найдено")
    else:
        # Выходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)


@dp.message_handler(state=BotStates.EVAL_EVENT_STATE)
async def score_event(msg: types.Message):
    global _temp

    if msg.text != "В главное меню":
        # Если оценка находится в корректном диапазоне от 1 до 5
        if msg.text in "12345":
            # Добавляем оценку
            _temp[1] += f'{msg.text};'

            # Обновляем оценки мероприятия
            cursor.execute(f'''UPDATE Events SET scores = ? WHERE title = ?''',
                           (_temp[1], _temp[0]))
            conn.commit()

            # Отправляем сообщение
            await bot.send_message(
                msg.from_user.id,
                f"Оценка \"{msg.text}\" мероприятию " +
                f"\"{_temp[0]}\" поставлена!")

            # "Обнуляем" временную переменную
            _temp = None

            # Переходим в главное меню
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.START_STATE)
            await start(msg)
        # И если не находится
        else:
            # Отправляем сообщение об ошибке
            await bot.send_message(msg.from_user.id, "Неверное значение!")
    else:
        # Выходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)


@dp.message_handler(state=BotStates.CHOICE_FORUM_DATE_FOR_SING_UP_FOR_EVENT)
async def score_event(msg: types.Message):
    if msg.text != "В главное меню":
        # Берем все мероприятия за введённую дату
        events = cursor.execute(f''' SELECT * FROM Events WHERE date=? AND
                                entryIsOpen=? AND city=?''',
                                (msg.text, 1, user_city)).fetchall()

        send_text = "Выбери мероприятие:\n"
        keyboard = ReplyKeyboardMarkup()

        # Читаем JSON-файл с участниками мероприятий
        with open('./res/data/participants_of_events.json',
                  'r', encoding='utf-8') as participants_of_events:
            # Читаем файл
            data = json.load(participants_of_events)

        user_id = getValueByTgID(tgID=msg.from_user.id)
        for event in events:
            # Если мероприятие есть в JSON-файле и
            # на него не зарегистрирован пользователь
            # или если мероприятия нет в JSON-файле
            if (event[0] in data and
                user_id not in data[event[0]]) or \
                    (event[0] not in data):

                # Формируем клавиатуру со списком мероприятий
                keyboard.add(KeyboardButton(event[0]))

        keyboard.add(KeyboardButton("В главное меню"))

        # Если найдены доступные к регистрации мероприятия
        if send_text != "Выбери мероприятие:":
            # Отправляем список мероприятий на выбранный день
            await bot.send_message(msg.from_user.id,
                                   send_text,
                                   reply_markup=keyboard)

            # Переходим на этап выбора мероприятия
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.CHOICE_EVENT_SING_UP_FOR_EVENT)
        # И если нет
        else:
            await bot.send_message(msg.from_user.id,
                                   "На выбранный день " +
                                   "нет доступных мероприятий")
    else:
        # Переходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)


@dp.message_handler(state=BotStates.CHOICE_EVENT_SING_UP_FOR_EVENT)
async def score_event(msg: types.Message):
    if msg.text != "В главное меню":
        # Если такое мепроприятие существует
        if cursor.execute(f''' SELECT * FROM Events WHERE title = ? AND
                          entryIsOpen = ? AND city=?''',
                          (msg.text, 1, user_city)).fetchall():
            # Открываем JSON со структурой
            # Мероприятие: [участник 1, участник 2...]
            with open('./res/data/participants_of_events.json',
                      'r', encoding='utf-8') as participants_of_events:
                # Читаем файл
                data = json.load(participants_of_events)

            # Получаем ID пльзователя
            user_id = getValueByTgID("UsersInfo", "id", msg.from_user.id)

            # Добавляем участника на мероприятие,
            # если на это мероприятие уже кто-то регистрировался
            if msg.text in data:
                data[msg.text].append(user_id)
            # И если нет
            else:
                data[msg.text] = [user_id]

            # Обновляем JSON-файл
            with open('./res/data/participants_of_events.json',
                      'w', encoding='utf-8') as participants_of_events:
                json.dump(data,
                          participants_of_events,
                          indent=4,
                          ensure_ascii=False)

            # Берём текущее количество участников
            currentParticipantsCounter = \
                cursor.execute(f''' SELECT currentParticipants FROM Events
                               WHERE title=? AND city=?''',
                               (msg.text, user_city)).fetchall()[0][0]

            # Обновляем текущее число участников у мероприятия
            cursor.execute(f'''UPDATE Events SET currentParticipants = ?
                           WHERE title=? AND city=?''',
                           (currentParticipantsCounter + 1, msg.text,
                            user_city))
            conn.commit()

            # Отправляем сообщение об успешной регистрации
            # участника на мероприятие
            await bot.send_message(msg.from_user.id,
                                   "Вы успешно зарегистрировались " +
                                   f"на мероприятие \"{msg.text}\"")

            # Рассылаем уведомление о количестве мест,
            # если места на мероприятие заполнено на 75%
            maxtParticipantsCounter = \
                cursor.execute(f''' SELECT maxParticipants FROM Events
                               WHERE title = ? AND city=?''',
                               (msg.text, user_city)).fetchall()[0][0]

            if currentParticipantsCounter / \
                    maxtParticipantsCounter * 100 >= 75:
                users_tg_id = cursor.execute("""SELECT tg_id FROM UsersInfo
                                             WHERE tg_id <> ?""", ("None",))\
                                                .fetchall()

                for user_tg_id in users_tg_id:
                    if user_tg_id[0] != msg.from_user.id:
                        send_notify(TOKEN,
                                    PLACE_FOR_WORKSHOP_ENDS,
                                    user_tg_id[0])

            # Переходим в главное меню
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.START_STATE)
            await start(msg)
        # И если не существует
        else:
            # Отправляем сообщение об ошибке
            await bot.send_message(msg.from_user.id,
                                   "Мероприятие не найдено")
    else:
        # Переходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)


@dp.message_handler(state=BotStates.CHOICE_FORUM_DATE_FOR_GET_MY_EVENTS)
async def score_event(msg: types.Message):
    if msg.text != "В главное меню":
        # Берём список мероприятий за выбранный день
        events_by_date = \
            cursor.execute(f''' SELECT * FROM Events
                           WHERE date=? AND city=?''',
                           (msg.text, user_city)).fetchall()

        send_text = f"Твои мероприятия на {msg.text}:"
        # Открываем JSON со структурой Мероприятие: [участник 1, участник 2...]
        with open('./res/data/participants_of_events.json',
                  'r', encoding='utf-8') as participants_of_events:
            # Читаем файл
            data = json.load(participants_of_events)

        # Перебираем мероприятия за этот день
        for event in events_by_date:
            # Берем его название
            event_title = event[0]

            # Если это название уже есть в JSON
            if event_title in data:
                # Если ID пользователя уже добавлен в список участников
                # этого мероприятия
                if getValueByTgID(tgID=msg.from_user.id) in data[event_title]:
                    # Формируем сообщение
                    send_text += f"\n✅ {event[0]}\n" + \
                        f"Описание: {event[1]}\n" + \
                        f"Время: {event[3]} - {event[4]}\n" + \
                        f"Место: {event[5]}\n"

        # Если найдены мероприятия
        if send_text != f"Твои мероприятия на {msg.text}:":
            # Отправляем сообщение со списком мероприятий,
            # где зарегистрирован пользователь
            await bot.send_message(msg.from_user.id, send_text)
        # А если не найдены
        else:
            await bot.send_message(msg.from_user.id,
                                   f"Твои мероприятия на {msg.text}" +
                                   " не найдены! Пройди регистрацию " +
                                   " на воркшопы, походящие в данный день.")

    # Переходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp)
