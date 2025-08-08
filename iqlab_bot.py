import telebot
from telebot import types
from datetime import datetime, timedelta

TOKEN = '8207596553:AAH8wcoqshmnUwS1Zrq_rL3e_LnrLPnW6mg'
CHANNEL_ID = -1002738907591  # Встав сюди свій канал/чат ID

bot = telebot.TeleBot(TOKEN)

# Структура категорій і аналізів
categories = {
    "Загальні аналізи": ["Загальний аналіз крові", "Загальний аналіз сечі"],
    "Біохімія": ["Білірубін", "Глюкоза", "Холестерин"],
    "Інфекції": ["Гепатит B", "Гепатит C", "ВІЛ"],
}

user_data = {}
queue_number = 0  # Номер черги

def get_date_buttons():
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        btn = types.InlineKeyboardButton(date.strftime("%d-%m-%Y"), callback_data=f"date_{date.strftime('%Y-%m-%d')}")
        markup.add(btn)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "category"}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in categories.keys():
        markup.add(types.KeyboardButton(cat))
    bot.send_message(user_id, "Виберіть категорію аналізів:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text

    if user_id not in user_data:
        bot.send_message(user_id, "Натисніть /start для початку.")
        return

    step = user_data[user_id].get("step")

    if step == "category":
        if text not in categories:
            bot.send_message(user_id, "Оберіть категорію з кнопок.")
            return
        user_data[user_id]["category"] = text
        user_data[user_id]["step"] = "analysis"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for analysis in categories[text]:
            markup.add(types.KeyboardButton(analysis))
        markup.add(types.KeyboardButton("Назад"))
        bot.send_message(user_id, "Оберіть аналіз:", reply_markup=markup)

    elif step == "analysis":
        if text == "Назад":
            user_data[user_id]["step"] = "category"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for cat in categories.keys():
                markup.add(types.KeyboardButton(cat))
            bot.send_message(user_id, "Виберіть категорію аналізів:", reply_markup=markup)
            return

        category = user_data[user_id].get("category")
        if category is None or text not in categories[category]:
            bot.send_message(user_id, "Оберіть аналіз з кнопок.")
            return
        user_data[user_id]["analysis"] = text
        user_data[user_id]["step"] = "date"
        bot.send_message(user_id, "Оберіть дату відвідування:", reply_markup=get_date_buttons())

    elif step == "confirmed":
        bot.send_message(user_id, "Ви вже записані. Якщо хочете записатися знову, натисніть /start")

@bot.callback_query_handler(func=lambda call: call.data.startswith("date_"))
def handle_date(call):
    user_id = call.from_user.id
    if user_id not in user_data or user_data[user_id].get("step") != "date":
        bot.answer_callback_query(call.id, "Будь ласка, почніть запис командою /start")
        return

    date_str = call.data[5:]  # 'YYYY-MM-DD'
    user_data[user_id]["date"] = date_str
    user_data[user_id]["step"] = "confirm"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Готово"))
    markup.add(types.KeyboardButton("Назад"))

    summary = (
        f"Підтвердіть запис:\n"
        f"Категорія: {user_data[user_id]['category']}\n"
        f"Аналіз: {user_data[user_id]['analysis']}\n"
        f"Дата: {date_str}\n\n"
        f"Натисніть 'Готово' для підтвердження або 'Назад' для редагування."
    )

    bot.send_message(user_id, summary, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_confirm(message):
    user_id = message.from_user.id
    text = message.text

    if user_id not in user_data:
        bot.send_message(user_id, "Натисніть /start для початку.")
        return

    step = user_data[user_id].get("step")
    if step != "confirm":
        return  # Ігноруємо повідомлення на інших кроках

    if text == "Назад":
        user_data[user_id]["step"] = "date"
        bot.send_message(user_id, "Оберіть дату відвідування:", reply_markup=get_date_buttons())
        return

    if text == "Готово":
        global queue_number
        queue_number += 1

        user_data[user_id]["step"] = "confirmed"
        user_data[user_id]["queue_number"] = queue_number

        confirmation = (
            f"Ви успішно записані!\n"
            f"Ваш номер у черзі: {queue_number}\n"
            f"Категорія: {user_data[user_id]['category']}\n"
            f"Аналіз: {user_data[user_id]['analysis']}\n"
            f"Дата: {user_data[user_id]['date']}"
        )

        bot.send_message(user_id, confirmation, reply_markup=types.ReplyKeyboardRemove())

        # Відправка в канал
        text_to_channel = (
            f"Нова запис на аналізи:\n"
            f"Користувач: @{message.from_user.username if message.from_user.username else message.from_user.first_name}\n"
            f"Номер у черзі: {queue_number}\n"
            f"Категорія: {user_data[user_id]['category']}\n"
            f"Аналіз: {user_data[user_id]['analysis']}\n"
            f"Дата: {user_data[user_id]['date']}"
        )
        bot.send_message(CHANNEL_ID, text_to_channel)

        return

    bot.send_message(user_id, "Будь ласка, натисніть 'Готово' або 'Назад'.")

bot.polling()


