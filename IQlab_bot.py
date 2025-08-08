import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

TOKEN = 'YOUR_BOT_TOKEN'
ADMIN_CHAT_ID = '123456789'  # Замените на свой Telegram ID

bot = telebot.TeleBot(TOKEN)

BASE_URL = 'https://iqlab.com.ua/catalog'
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

def get_categories():
    r = requests.get(BASE_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    categories = []
    for cat in soup.select('.catalog-section__item'):
        title = cat.select_one('.catalog-section__title')
        if title:
            name = title.text.strip()
            url = 'https://iqlab.com.ua' + title['href']
            categories.append({'name': name, 'url': url})
    return categories

def get_tests(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    rows = soup.select('table.table > tbody > tr')
    tests = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 3:
            tests.append({
                'name': cols[0].text.strip(),
                'term': cols[1].text.strip(),
                'price': cols[2].text.strip()
            })
    return tests

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
    cats = get_categories()
    user_selection[uid]['cats'] = cats
    bot.send_message(uid, "👋 Вітаємо у Telegram-боті лабораторії!")
    bot.send_message(uid, OFFICE_INFO, parse_mode="Markdown")
    bot.send_message(uid, "🔽 Оберіть категорію:", reply_markup=kb([c['name'] for c in cats]))

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == 'cat')
def cat(m):
    uid = m.chat.id
    cat = next((c for c in user_selection[uid]['cats'] if c['name'] == m.text), None)
    if not cat:
        return bot.send_message(uid, "❗ Будь ласка, оберіть категорію зі списку.")
    user_selection[uid]['cat'] = cat
    tests = get_tests(cat['url'])
    user_selection[uid]['all_tests'] = tests
    user_state[uid] = 'test'
    bot.send_message(uid, "🧪 Оберіть аналіз (по одному). Коли закінчите — натисніть 'Готово'", reply_markup=kb([t['name'] for t in tests[:20]] + ['Готово']))

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
    # Отправка админу
    user = m.from_user
    admin_msg = f"📥 Нова заявка:\n👤 {user.first_name} (@{user.username or '—'})\n📅 {date_str}\n{msg}"
    bot.send_message(ADMIN_CHAT_ID, admin_msg)
    user_state.pop(uid)
    user_selection.pop(uid)

bot.polling()
