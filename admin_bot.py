from notifiers import get_notifier
from res.config_reader import config

from aiogram import Bot, types, Dispatcher, executor

import sqlite3

TOKEN = config.bot_token.get_secret_value()
ADMIN_TOKEN = config.admin_bot_token.get_secret_value()

# Объект бота
bot = Bot(token=ADMIN_TOKEN)
# Диспетчер
dp = Dispatcher(bot)

# Подгружаем БД
conn = sqlite3.connect('res/db/PoleOfKnowledge_db.db')
cursor = conn.cursor()

# Аккаунты-администраторы
ADMIN_ID = cursor.execute(f''' SELECT * FROM Admin''').fetchall()


def send_notify(token: str, msg: str, chatId: int):
    telegram = get_notifier('telegram')
    telegram.notify(
        token=token,
        chat_id=chatId,
        message=msg)


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await bot.send_message(msg.from_user.id, "Отправьте сообщение")


# Хэндлер на текстовые сообщения
@dp.message_handler()
async def reply_to_text_msg(msg: types.Message):
    cursor.execute(
        f''' SELECT * FROM UsersInfo''')
    users = cursor.fetchall()
    for user in users:
        send_notify(token=TOKEN, msg=msg.text, chatId=user[0])


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp)
