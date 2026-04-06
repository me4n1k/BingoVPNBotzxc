import telebot
import json
import os
from datetime import datetime, timedelta

TOKEN = "8734333699:AAGkhTCZzt2B8vgaOcy-vNtjr1gRb-dmPtA"
ADMIN_ID = 7984475695
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "users_data.json"

waiting_for_link = {}

SUBSCRIPTIONS = {
    "1 месяц": {"name": "1 месяц", "days": 30, "price": 40, "display": "💳 1 месяц - 30 дней - 40 ₽"},
    "3 месяца": {"name": "3 месяца", "days": 90, "price": 115, "display": "💳 3 месяца - 90 дней - 115 ₽"},
    "6 месяцев": {"name": "6 месяцев", "days": 180, "price": 225, "display": "💳 6 месяцев - 180 дней - 225 ₽"},
    "12 месяцев": {"name": "12 месяцев", "days": 360, "price": 450, "display": "💳 12 месяцев - 360 дней - 450 ₽"}
}


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_data(user_id):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "subscriptions": []
        }
        save_data(data)
    return data[user_id_str]


def add_subscription(user_id, sub_type):
    data = load_data()
    user_id_str = str(user_id)
    now = datetime.now()
    days = SUBSCRIPTIONS[sub_type]["days"]
    end_date = now + timedelta(days=days)
    subscription = {
        "type": sub_type,
        "start": now.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d")
    }
    if user_id_str not in data:
        data[user_id_str] = {
            "first_seen": now.strftime("%Y-%m-%d %H:%M:%S"),
            "subscriptions": []
        }
    data[user_id_str]["subscriptions"].append(subscription)
    save_data(data)
    return subscription


def get_active_subscriptions(user_id):
    user_data = get_user_data(user_id)
    active = []
    today = datetime.now().date()
    for sub in user_data["subscriptions"]:
        end_date = datetime.strptime(sub["end"], "%Y-%m-%d").date()
        if end_date >= today:
            active.append(sub)
    return active


# Прозрачные кнопки под сообщением
def main_menu():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"),
        telebot.types.InlineKeyboardButton("💳 Купить", callback_data="menu_buy"),
        telebot.types.InlineKeyboardButton("📋 Мои подписки", callback_data="menu_subs")
    )
    return keyboard


def welcome_message():
    return """👋 Добро пожаловать в Bingo VPN 🚀

Безопасный и быстрый интернет с подключением по ссылке ⚡

✅ Что внутри:
• Скорость до 1 Гбит/с ⚡️
• Приложения для Android, iOS, Windows, macOS, Linux 📲
• Без логов трафика 🔒
• Большое количество серверов💰

👇 Выберите действие:"""


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    bot.send_message(message.chat.id, welcome_message(), reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu(call):
    if call.data == "menu_profile":
        user_id = call.from_user.id
        user_data = get_user_data(user_id)
        active_subs = get_active_subscriptions(user_id)

        if active_subs:
            subs_text = ""
            for sub in active_subs:
                sub_name = SUBSCRIPTIONS[sub["type"]]["name"]
                subs_text += f"\n   • {sub_name} ({sub['start']} - {sub['end']})"
        else:
            subs_text = "\n   • нет"

        text = f"""👤 Ваш профиль
--------------------------------------------
🆔 ID: {user_id}

📅 Зарегистрирован: {user_data['first_seen']}

💳 Ваши активные подписки:{subs_text}"""

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        bot.answer_callback_query(call.id)

    elif call.data == "menu_buy":
        text = """🚀 Безопасный доступ в интернет — просто и быстро!

👇 Выберите тариф:"""

        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            telebot.types.InlineKeyboardButton("💳 1 месяц - 40 ₽", callback_data="buy_1 месяц"),
            telebot.types.InlineKeyboardButton("💳 3 месяца - 115 ₽", callback_data="buy_3 месяца"),
            telebot.types.InlineKeyboardButton("💳 6 месяцев - 225 ₽", callback_data="buy_6 месяцев"),
            telebot.types.InlineKeyboardButton("💳 12 месяцев - 450 ₽", callback_data="buy_12 месяцев"),
            telebot.types.InlineKeyboardButton("◀️ Назад", callback_data="menu_back")
        )

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        bot.answer_callback_query(call.id)

    elif call.data == "menu_subs":
        user_id = call.from_user.id
        active_subs = get_active_subscriptions(user_id)

        if active_subs:
            text = "📋 Ваши активные подписки:\n\n"
            for sub in active_subs:
                sub_name = SUBSCRIPTIONS[sub["type"]]["name"]
                text += f"• {sub_name}\n"
                text += f"  📅 {sub['start']} - {sub['end']}\n\n"
        else:
            text = "📭 У вас нет активных подписок"

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        bot.answer_callback_query(call.id)

    elif call.data == "menu_back":
        bot.edit_message_text(welcome_message(), call.message.chat.id, call.message.message_id,
                              reply_markup=main_menu())
        bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy(call):
    user_id = call.from_user.id
    sub_type = call.data.replace("buy_", "")
    sub_info = SUBSCRIPTIONS[sub_type]
    sub_name = sub_info["name"]
    price = sub_info["price"]

    text = f"""✅ Вы выбрали подписку: *{sub_name}*
💰 Сумма: {price} ₽

📌 Инструкция по оплате:

1️⃣ Перейдите по ссылке:
🔗 https://www.donationalerts.com/r/me4n1k

2️⃣ Укажите сумму: *{price} ₽*

3️⃣ В комментарии к донату напишите:
`{sub_name} {user_id}`

4️⃣ Нажмите «Я оплатил»

🕒 VPN выдадут в течение 24 часов"""

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        telebot.types.InlineKeyboardButton("🔗 Перейти к оплате", url="https://www.donationalerts.com/r/me4n1k"),
        telebot.types.InlineKeyboardButton("📤 Я оплатил", callback_data=f"paid_{sub_type}_{user_id}"),
        telebot.types.InlineKeyboardButton("◀️ Назад", callback_data="menu_buy")
    )

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard,
                          parse_mode="Markdown")
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def handle_paid(call):
    parts = call.data.split("_")
    sub_type = parts[1]
    user_id = int(parts[2])
    sub_name = SUBSCRIPTIONS[sub_type]["name"]
    price = SUBSCRIPTIONS[sub_type]["price"]

    admin_text = f"""🟢 НОВАЯ ЗАЯВКА НА ОПЛАТУ!

👤 Пользователь: [{user_id}](tg://user?id={user_id})
💳 Тариф: {sub_name}
💰 Сумма: {price} ₽

✅ Команда: `/add_sub {user_id} {sub_type}`"""

    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

    bot.answer_callback_query(call.id, "✅ Заявка отправлена!")
    bot.edit_message_text(
        f"✅ Заявка на '*{sub_name}*' отправлена!\n"
        f"🕒 VPN выдадут в течение 24 часов",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['add_sub'])
def admin_add_sub(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Нет прав")
        return
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ /add_sub ID тариф\nПример: /add_sub 7984475695 1 месяц")
            return

        user_id = int(parts[1])
        sub_type = parts[2].strip()

        if sub_type not in SUBSCRIPTIONS:
            bot.reply_to(message, f"❌ Доступны: 1 месяц, 3 месяца, 6 месяцев, 12 месяцев")
            return

        waiting_for_link[message.from_user.id] = {"user_id": user_id, "sub_type": sub_type}
        bot.reply_to(message, f"📝 Отправьте ссылку для пользователя {user_id}:")

    except:
        bot.reply_to(message, "❌ Ошибка")


@bot.message_handler(func=lambda message: message.from_user.id in waiting_for_link)
def handle_vpn_link(message):
    admin_id = message.from_user.id
    vpn_link = message.text.strip()

    data = waiting_for_link[admin_id]
    user_id = data["user_id"]
    sub_type = data["sub_type"]

    del waiting_for_link[admin_id]

    subscription = add_subscription(user_id, sub_type)

    bot.reply_to(message, f"✅ Подписка добавлена пользователю {user_id}\n📅 До {subscription['end']}")

    try:
        bot.send_message(user_id,
                         f"✅ Ваша подписка '{SUBSCRIPTIONS[sub_type]['name']}' активирована!\n"
                         f"📅 Действует до: {subscription['end']}\n\n"
                         f"🔗 Ваша ссылка для подключения:\n{vpn_link}\n\n"
                         f"Спасибо за покупку! 🎉")
    except:
        pass


@bot.message_handler(commands=['list_users'])
def admin_list_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Нет прав")
        return
    data = load_data()
    if not data:
        bot.reply_to(message, "Нет пользователей")
        return
    text = "📋 Список пользователей:\n\n"
    for uid, info in data.items():
        active_count = 0
        for sub in info["subscriptions"]:
            if datetime.strptime(sub["end"], "%Y-%m-%d").date() >= datetime.now().date():
                active_count += 1
        text += f"🆔 {uid} | подписок: {active_count}\n"
    bot.send_message(message.chat.id, text[:4000])


print("🤖 Бот запущен!")
bot.infinity_polling()