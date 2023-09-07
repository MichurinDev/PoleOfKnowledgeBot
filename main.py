# Импорты
from res.config_reader import config
from res.reply_texts import *
from res.SendNotify import send_notify

from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ParseMode, KeyboardButton, ReplyKeyboardMarkup, \
    InputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import sqlite3
import json
from random import choice

# Объект бота
TOKEN = config.bot_token.get_secret_value()
ADMIN_TOKEN = config.admin_bot_token.get_secret_value()

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
user_type = ""

# Пути до изображений карт площадок
forum_maps = {
    "Яр-Сале": "./res/forum_maps/yar_sale.jpg",
    "Надым": "./res/forum_maps/nadym.jpg",
    "Тарко-Сале": "./res/forum_maps/tarko_sale.jpg"
}

# Кнопки главного меню
buttons = [
    'Карта площадки',
    'Показать расписание',
    'Записаться на воркшопы',
    'Мои мероприятия',
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

    SEND_MSG_TO_SUPPORT = State()


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
    global user_city, user_type

    # Берём список всех зарегистрированных пользователей с выборков по ID
    user_by_tgID = cursor.execute(f''' SELECT name FROM UsersInfo
                           WHERE tg_id={msg.from_user.id}''').fetchall()

    state = dp.current_state(user=msg.from_user.id)

    if user_by_tgID:
        # Формируем клавиатуру с меню по боту
        keyboard = ReplyKeyboardMarkup()
        for btn in buttons:
            if (btn != buttons[2] and btn != buttons[3]) or\
                    (btn == buttons[2] and
                     getValueByTgID(value_column="type",
                                    tgID=msg.from_user.id) == "Ученик") or\
                    (btn == buttons[3] and
                     getValueByTgID(value_column="type",
                                    tgID=msg.from_user.id) == "Ученик"):
                keyboard.add(KeyboardButton(btn))

        # Отправляем ее вместе с приветственным сообщением
        # для зарегистрированного пользователя
        if msg.text == "/start":
            await bot.send_message(
                msg.from_user.id, f"Привет-привет!")

        user_city = getValueByTgID(value_column="city", tgID=msg.from_user.id)
        user_type = getValueByTgID(value_column="type", tgID=msg.from_user.id)

        await bot.send_message(msg.from_user.id,
                               MENU_TEXT, reply_markup=keyboard)
        await state.set_state(BotStates.HOME_STATE.state)

    else:
        # Отправляем текст с предложением ввести ID
        await bot.send_message(
            msg.from_user.id,
            START_TEXT,
            parse_mode=ParseMode.MARKDOWN)

        # Переходим на стадию ввода ID
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
        map_path = forum_maps[user_city]
        map = InputFile(path_or_bytesio=map_path,
                        filename=f"{user_city}_map.jpg")

        await bot.send_photo(msg.from_user.id, map,
                             caption="Лови карту своей площадки!")
    elif msg.text == buttons[1]:
        await bot.send_message(msg.from_user.id, choice(TIMETABLE_TITLE_TEXTS))

        send_text = ""

        # Берем все мероприятия по городу
        events = cursor.execute(f''' SELECT title, description, start, end,
                                place, invitedUserTypes FROM Events
                                WHERE city=?''', (user_city,)).fetchall()

        if user_type != "Администратор":
            invited_events = list(filter(lambda x: user_type in x[5], events))
        else:
            invited_events = list(filter(lambda x: "" in x[5], events))

        if invited_events:
            for event in invited_events:
                send_text += f"\n✅ {event[0]}\n" + \
                    f"Описание: {event[1]}\n" + \
                    f"Время: {event[2]} - {event[3]}\n" + \
                    f"Место: {event[4]}\n"
        else:
            send_text = "Мероприятия не найдены!"

        await bot.send_message(msg.from_user.id, send_text)
    elif msg.text == buttons[2]:
        if getValueByTgID(
                value_column="type", tgID=msg.from_user.id) == "Ученик":
            if not cursor.execute('''SELECT workshop FROM UsersInfo
                                  WHERE type="Ученик" AND
                                  workshop="Null"''').fetchall():
                # Берем все воркшопы в городе
                events = cursor.execute(''' SELECT * FROM Workshops WHERE
                                        entryIsOpen=? AND city=?''',
                                        (1, user_city)).fetchall()
                send_text = "Выбери воркшоп:"
                keyboard = ReplyKeyboardMarkup()

                for event in events:
                    keyboard.add(KeyboardButton(event[0]))

                keyboard.add(KeyboardButton("В главное меню"))

                # Отправляем список воркшопов
                await bot.send_message(msg.from_user.id,
                                       send_text,
                                       reply_markup=keyboard)

                state = dp.current_state(user=msg.from_user.id)
                await state.set_state(
                    BotStates.CHOICE_EVENT_SING_UP_FOR_EVENT)
            else:
                await bot.send_message(msg.from_user.id,
                                       "Ты уже выбрал воркшоп!")
        else:
            await bot.send_message(msg.from_user.id,
                                   "На воркшоп могут зарегистрироваться " +
                                   "только ученики!")
    elif msg.text == buttons[3]:
        send_text = "Воркшоп, на который ты зарегистрирован:"
        user_workshop = cursor.execute('''SELECT workshop FROM
                                       UsersInfo  WHERE tg_id=?
                                       AND workshop <> "None"''',
                                       (msg.from_user.id,)).fetchall()

        if user_workshop:
            send_text = "Воркшоп, на который ты зарегистрирован:" +\
                f"\n✅ {user_workshop[0][0]}"
        else:
            send_text = "Ты еще не зарегистрировался ни на один воркшоп!" +\
                " Скорее регистрируйся"

        await bot.send_message(msg.from_user.id, send_text)
    elif msg.text == buttons[4]:
        await bot.send_message(msg.from_user.id, "Текст про награды")
    elif msg.text == buttons[5]:
        # Берем все мероприятия в городе
        events = cursor.execute(f''' SELECT title, invitedUserTypes FROM
                                Events WHERE city=?''',
                                (user_city,)).fetchall()
        invited_events = list(filter(lambda x: user_type in x[1], events))

        send_text = f"Выбери мероприятие:\n"
        keyboard = ReplyKeyboardMarkup()

        for event in invited_events:
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
    elif msg.text == buttons[6]:
        await bot.send_message(msg.from_user.id, SUPPORT_TEXT)

        # Переходим на стадию отправки сообщения поддержке
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.SEND_MSG_TO_SUPPORT.state)
    elif msg.text == "/start":
        await start(msg)
    elif msg.text == "/help":
        await help(msg)


@dp.message_handler(state=BotStates.ACQUAINTANCE_STATE)
async def acquaintance_for_user(msg: types.Message):
    # Если незарегистрированый пользователь с введёным ID существует
    if cursor.execute('''SELECT name FROM UsersInfo
                      WHERE id=? AND tg_id IS NULL''',
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

        # Получаем тип и город пользователя
        user_type = getValueByTgID(value_column="type", tgID=msg.from_user.id)
        user_city = getValueByTgID(value_column="city", tgID=msg.from_user.id)

        # Если пользователь - ученик
        if user_type == "Ученик":
            # Получаем название команды
            teams = data[user_city]["students"]
            team_name = sorted(teams,
                               key=lambda s: len(teams[s]))[0]
            # Добавляем туда нового пользователя
            data[user_city]["students"][team_name].append(
                getValueByTgID(tgID=msg.from_user.id))

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
        elif user_type == "Учитель":
            team_name = "Фиолетовая звезда"
            data[user_city][team_name].append(
                getValueByTgID(tgID=msg.from_user.id))

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


@dp.message_handler(state=BotStates.CHOICE_EVENT_STATE)
async def choice_event(msg: types.Message):
    global _temp

    if msg.text != "В главное меню":
        event_scores = cursor.execute(f''' SELECT scores FROM Events
                                      WHERE title=? AND city=?''',
                                      (msg.text, user_city)).fetchall()
        # Если мероприятия с таким названием есть
        if event_scores:
            # Берем оценки мероприятия
            event_scores = event_scores[0][0]
            # Сохраняем название и оценки мероприятия
            _temp = [msg.text, event_scores]

            # Формируем клавиатуру
            keyboard = ReplyKeyboardMarkup()
            for i in range(1, 6):
                keyboard.add(KeyboardButton(str(i)))
            keyboard.add(KeyboardButton("В главное меню"))

            username = getValueByTgID(value_column='name',
                                      tgID=msg.from_user.id)
            # Отправляем сообщение
            await bot.send_message(
                msg.from_user.id,
                choice([
                    "Псссс… я тут слежу за порядком и качеством. Скажи, тебе" +
                    " понравилась эта площадка? Пройди, пожалуйста," +
                    " небольшой опрос.",

                    "Как здорово, что ты побывал тут! Расскажи о " +
                    "своих впечатлениях",

                    f"Ну что, {username}, " +
                    "как все прошло? Поделишься со мной эмоциями?",

                    "Эх, я совсем не успеваю сегодня обойти все площадки..." +
                    f" Расскажи мне, тебе понравилось на {msg.text}?"
                ]),
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
            cursor.execute(f'''UPDATE Events SET scores=?
                           WHERE title=? AND city=?''',
                           (_temp[1], _temp[0], user_city))
            conn.commit()

            # Отправляем сообщение
            await bot.send_message(msg.from_user.id, "Гав! Спасибо за оценку!")
            await bot.send_sticker(msg.from_user.id,
                                   "CAACAgIAAxkBAAEKMfxk8mJ" +
                                   "3O3ut2HeOGOwTrbPHQO8ycw" +
                                   "ACFDQAAu0RmEucG2GmeEXS6zAE")

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


@dp.message_handler(state=BotStates.CHOICE_EVENT_SING_UP_FOR_EVENT)
async def score_event(msg: types.Message):
    if msg.text != "В главное меню":
        workshop = cursor.execute('''SELECT currentParticipants,
                                  maxParticipants FROM Workshops
                                  WHERE title=? AND entryIsOpen=?
                                  AND city=?''',
                                  (msg.text, 1, user_city)).fetchall()

        # Если такое мепроприятие существует
        if workshop:
            cursor.execute('''UPDATE UsersInfo SET workshop=?
                           WHERE tg_id=?''',
                           (msg.text, msg.from_user.id))

            # Берём текущее количество участников
            currentParticipantsCounter = workshop[0][0] + 1

            # Обновляем текущее число участников у мероприятия
            cursor.execute('''UPDATE Workshops SET currentParticipants=?
                           WHERE title=? AND city=?''',
                           (currentParticipantsCounter, msg.text,
                            user_city))
            conn.commit()

            # Отправляем сообщение об успешной регистрации
            # участника на мероприятие
            await bot.send_message(msg.from_user.id,
                                   "Вы успешно зарегистрировались " +
                                   f"на мероприятие \"{msg.text}\"")

            # Рассылаем уведомление о количестве мест,
            # если места на мероприятие заполнено на 75%
            maxtParticipantsCounter = workshop[0][1]

            if currentParticipantsCounter / maxtParticipantsCounter >= 0.75:
                users_tg_id = cursor.execute("""SELECT tg_id FROM UsersInfo
                                             WHERE tg_id<>"None" AND city=?
                                             AND type="Ученик" """,
                                             (user_city, )).fetchall()

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
                                   "Воркшоп не найден!")
    else:
        # Переходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)


@dp.message_handler(state=BotStates.SEND_MSG_TO_SUPPORT)
async def score_event(msg: types.Message):
    if cursor.execute('''SELECT id FROM MsgToSupport''').fetchall():
        last_msg_id = cursor.execute('''SELECT id FROM MsgToSupport''')\
            .fetchall()[-1][0]
    else:
        last_msg_id = 0
    cursor.execute(f'''INSERT INTO MsgToSupport
                   (id, user_id, tg_id, name, city, message)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                   (
                    last_msg_id + 1,
                    getValueByTgID(tgID=msg.from_user.id),
                    msg.from_user.id,
                    getValueByTgID(value_column="name",
                                   tgID=msg.from_user.id),
                    user_city,
                    msg.text
                    ))
    conn.commit()

    support_users_tg_id = cursor.execute(f'''SELECT tg_id FROM UsersInfo
                                   WHERE type in ("Администратор", "Волонтёр")
                                   AND city=?''', (user_city,)).fetchall()

    for support_user_tg_id in support_users_tg_id:
        if support_user_tg_id[0]:
            send_notify(ADMIN_TOKEN,
                        "Пришло новое сообщение в поддержку!",
                        support_user_tg_id[0])

    await bot.send_message(msg.from_user.id, "Сообщение отправлено!")

    # Переходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=False)
