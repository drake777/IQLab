import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timedelta

TOKEN = '8207596553:AAH8wcoqshmnUwS1Zrq_rL3e_LnrLPnW6mg'
ADMIN_CHAT_ID = '1002738907591'  # Telegram ID администратора

bot = telebot.TeleBot(TOKEN)

user_state = {}
user_selection = {}

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

# 🔽 Категории и анализы вручную
CATEGORIES = {
    "Загальний аналіз крові": [
        {"name": "ЗАК (Загальний аналіз крові)", "term": "1 день", "price": "150 грн"},
        {"name": "Гемоглобін", "term": "1 день", "price": "100 грн"},
    ],
    "Біохімія": [
        {"name": "Глюкоза", "term": "1 день", "price": "120 грн"},
        {"name": "АСТ", "term": "1 день", "price": "130 грн"},
        {"name": "АЛТ", "term": "1 день", "price": "130 грн"},
    ],
    "Гормони": [
        {"name": "ТСГ (Тиреотропний гормон)", "term": "2 дні", "price": "220 грн"},
        {"name": "Т3 вільний", "term": "2 дні", "price": "240 грн"},
        {"name": "Т4 вільний", "term": "2 дні", "price": "240 грн"},
    ],
    "Сеча": [
        {"name": "Загальний аналіз сечі", "term": "1 день", "price": "100 грн"},
        {"name": "Добова білок у сечі", "term": "2 дні", "price": "150 грн"},
    ],
    "Інфекції": [
        {"name": "Гепатит B (HBsAg)", "term": "2 дні", "price": "300 грн"},
        {"name": "Гепатит C (anti-HCV)", "term": "2 дні", "price": "300 грн"},
    ]
}

def kb(items):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for item in items:
        markup.add(KeyboardButton(item))
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.chat.id
    user_state[uid] = 'cat'
    user_selection[uid] = {'tests': []}
    categories = list(CATEGORIES.keys())
    user_selection[uid]['cats'] = categories
    bot.send_message(uid, "👋 Вітаємо у Telegram-боті лабораторії!")
    bot.send_message(uid, OFFICE_INFO, parse_mode="Markdown")
    bot.send_message(uid, "🔽 Оберіть категорію:", reply_markup=kb(categories))

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == 'cat')
def cat(m):
    uid = m.chat.id
    if m.text not in CATEGORIES:
        return bot.send_message(uid, "❗ Будь ласка, оберіть категорію зі списку.")
    user_selection[uid]['cat'] = m.text
    tests = CATEGORIES[m.text]
    user_selection[uid]['all_tests'] = tests
    user_state[uid] = 'test'
    bot.send_message(uid, "🧪 Оберіть аналіз (по одному). Коли закінчите — натисніть 'Готово'", reply_markup=kb([t['name'] for t in tests] + ['Готово']))

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == 'test')
def test(m):
    uid = m.chat.id
    if m.text == 'Готово':
        if not user_selection[uid]['tests']:
            return bot.send_message(uid, "⚠️ Оберіть хоча б один аналіз.")
        user_state[uid] = 'date'
        today = datetime.today()
        dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
        return bot.send_message(uid, "📅 Оберіть дату відвідування:", reply_markup=kb(dates))
    test = next((t for t in user_selection[uid]['all_tests'] if t['name'] == m.text), None)
    if test and test not in user_selection[uid]['tests']:
        user_selection[uid]['tests'].append(test)
        bot.send_message(uid, f"✅ Додано: {test['name']}")
    else:
        bot.send_message(uid, "🧪 Оберіть аналіз із запропонованих або натисніть 'Готово'.")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == 'date')
def date(m):
    uid = m.chat.id
    try:
        d = datetime.strptime(m.text, '%Y-%m-%d').date()
        if d > datetime.today().date() + timedelta(days=30):
            raise ValueError
    except:
        return bot.send_message(uid, "❌ Некоректна дата. Введіть дату у форматі YYYY-MM-DD.")
    user_selection[uid]['date'] = d
    tests = user_selection[uid]['tests']
    msg = "\n".join([f"- {t['name']} (Срок: {t['term']}, Ціна: {t['price']})" for t in tests])
    date_str = d.strftime('%Y-%m-%d')
    final = f"🗓 *Запис на {date_str}*\n{msg}"
    bot.send_message(uid, OFFICE_INFO, parse_mode="Markdown")
    bot.send_message(uid, final, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    user = m.from_user
    admin_msg = f"📥 Нова заявка:\n👤 {user.first_name} (@{user.username or '—'})\n📅 {date_str}\n{msg}"
    bot.send_message(ADMIN_CHAT_ID, admin_msg)
    user_state.pop(uid)
    user_selection.pop(uid)

bot.polling()


