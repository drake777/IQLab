import telebot
from telebot import types
from datetime import datetime, timedelta

API_TOKEN = 'ТВОЙ_ТОКЕН_ТУТ'
CHANNEL_ID = '@твій_канал_або_chat_id'  # куда пересылать запись

bot = telebot.TeleBot(API_TOKEN)

OFFICE_INFO = """
🏥 *Медичний офіс*
📍 Дніпропетровська область, м. Підгородне
📌 вул. Центральна, 43б

🕒 *Час роботи:*
ПН-ПТ: 7:00 - 13:00  
Забір біоматеріалу: 7:00 - 11:00

СБ: 8:00 - 13:00  
Забір біоматеріалу: 8:00 - 11:00

НД: Вихідний
"""

# Пример категорий и анализов — можно менять на свои
CATEGORIES = {
    "Загальні аналізи": ["Загальний аналіз крові", "Загальний аналіз сечі"],
    "Біохімія": ["Глюкоза", "Холестерин"],
    "Інші": ["Тест на вагітність", "Аналіз на гормони"]
}

# Для простоты хранить данные пользователя здесь (для demo)
user_data = {}
queue_number = 1  # счетчик очереди

def get_dates_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        text = date.strftime("%d.%m.%Y")
        callback_data = f"date_{text}"
        markup.add(types.InlineKeyboardButton(text=text, callback_data=callback_data))
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_categories"))
    return markup

def get_categories_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat in CATEGORIES.keys():
        markup.add(types.InlineKeyboardButton(cat, callback_data=f"category_{cat}"))
    return markup

def get_analysis_keyboard(category):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for anal in CATEGORIES[category]:
        markup.add(types.InlineKeyboardButton(anal, callback_data=f"analysis_{anal}"))
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_categories"))
    return markup

def get_confirm_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Підтвердити", callback_data="confirm"))
    markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_analysis"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    global queue_number
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, OFFICE_INFO, parse_mode='Markdown')
    bot.send_message(message.chat.id, "Оберіть категорію аналізів:", reply_markup=get_categories_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global queue_number
    chat_id = call.message.chat.id

    if call.data.startswith("category_"):
        category = call.data.split("category_")[1]
        user_data[chat_id]['category'] = category
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f"Оберіть дату відвідування:", reply_markup=get_dates_keyboard())

    elif call.data.startswith("date_"):
        date = call.data.split("date_")[1]
        user_data[chat_id]['date'] = date
        category = user_data[chat_id].get('category')
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f"Оберіть аналіз з категорії *{category}*:", parse_mode='Markdown',
                              reply_markup=get_analysis_keyboard(category))

    elif call.data.startswith("analysis_"):
        analysis = call.data.split("analysis_")[1]
        user_data[chat_id]['analysis'] = analysis
        date = user_data[chat_id].get('date')
        category = user_data[chat_id].get('category')
        text = (f"Ви обрали:\nКатегорія: *{category}*\nДата: *{date}*\nАналіз: *{analysis}*\n\n"
                "Натисніть «Підтвердити», щоб записатися.")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=text, parse_mode='Markdown', reply_markup=get_confirm_keyboard())

    elif call.data == "confirm":
        # Присвоюємо номер черги
        number = queue_number
        queue_number += 1

        category = user_data[chat_id].get('category')
        date = user_data[chat_id].get('date')
        analysis = user_data[chat_id].get('analysis')

        ticket_text = (f"Номер черги: *{number}*\n"
                       f"Категорія: {category}\n"
                       f"Дата відвідування: {date}\n"
                       f"Аналіз: {analysis}\n"
                       f"Користувач: @{call.from_user.username if call.from_user.username else call.from_user.first_name}")

        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text="Запис успішно створено!\n\n" + ticket_text, parse_mode='Markdown')

        # Пересилання талону в канал
        bot.send_message(CHANNEL_ID, ticket_text, parse_mode='Markdown')

        # Очищуємо дані користувача
        user_data.pop(chat_id, None)

    elif call.data == "back_to_categories":
        user_data[chat_id].pop('category', None)
        user_data[chat_id].pop('date', None)
        user_data[chat_id].pop('analysis', None)
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text="Оберіть категорію аналізів:", reply_markup=get_categories_keyboard())

    elif call.data == "back_to_analysis":
        category = user_data[chat_id].get('category')
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f"Оберіть аналіз з категорії *{category}*:", parse_mode='Markdown',
                              reply_markup=get_analysis_keyboard(category))

if __name__ == '__main__':
    print("Бот запущено...")
    bot.infinity_polling()




