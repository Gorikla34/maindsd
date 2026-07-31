import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
import json
import os
import time

BOT_TOKEN = "8637077951:AAHPNai4n1s49BdpP4WCd8tk3UYJe5spAQA"
bot = telebot.TeleBot(BOT_TOKEN)

# ===== ФАЙЛЫ =====
ORDERS_FILE = "orders.json"
BALANCE_FILE = "balances.json"

def load_data(filename, default):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

orders = load_data(ORDERS_FILE, {})
balances = load_data(BALANCE_FILE, {})

def get_balance(user_id):
    return balances.get(str(user_id), 0)

def add_balance(user_id, amount):
    uid = str(user_id)
    balances[uid] = balances.get(uid, 0) + amount
    save_data(BALANCE_FILE, balances)

# ===== МЕНЮ =====
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎁 Магазин", callback_data="shop"),
        InlineKeyboardButton("👥 Рефералы", callback_data="refs"),
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("📊 Статистика", callback_data="stats")
    )
    return markup

def shop_categories():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🧸 Классика", callback_data="cat_classic"),
        InlineKeyboardButton("🏆 Статус", callback_data="cat_status"),
        InlineKeyboardButton("💎 Премиум", callback_data="cat_premium"),
        InlineKeyboardButton("🌟 Эксклюзив", callback_data="cat_exclusive"),
        InlineKeyboardButton("◀️ Назад", callback_data="main")
    )
    return markup

shop_items = {
    "classic": [
        ("🧸 Мишка", 15),
        ("❤️ Сердечко", 15),
        ("🌹 Роза", 25)
    ],
    "status": [
        ("🏆 Трофей", 50),
        ("🚀 Ракета", 50)
    ],
    "premium": [
        ("💍 Колечко", 80),
        ("💎 Алмаз", 80)
    ],
    "exclusive": [
        ("🖼️ NFT", 200)
    ]
}

def render_category(cat_key):
    markup = InlineKeyboardMarkup(row_width=2)
    for name, price in shop_items[cat_key]:
        markup.add(InlineKeyboardButton(f"{name} — {price}⭐", callback_data=f"buy_{name}_{price}"))
    markup.add(InlineKeyboardButton("◀️ Назад", callback_data="shop"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    ref_arg = message.text.split()
    if len(ref_arg) > 1:
        ref_id = ref_arg[1]
        if ref_id != user_id:
            add_balance(ref_id, 0.5)
            bot.send_message(ref_id, f"🎉 Новый реферал! +0.5⭐")

    bot.send_message(
        message.chat.id,
        "🛍️ *Добро пожаловать в PONCH1TA GIFTS!*\n"
        "Выберите действие:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = str(call.from_user.id)
    data = call.data

    if data == "main":
        bot.edit_message_text(
            "🛍️ *Главное меню*",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )

    elif data == "shop":
        bot.edit_message_text(
            "🎁 *Выберите категорию:*",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=shop_categories(),
            parse_mode="Markdown"
        )

    elif data in ["cat_classic", "cat_status", "cat_premium", "cat_exclusive"]:
        cat_map = {
            "cat_classic": "classic",
            "cat_status": "status",
            "cat_premium": "premium",
            "cat_exclusive": "exclusive"
        }
        cat = cat_map[data]
        bot.edit_message_text(
            f"🎁 *Подарки категории:*",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=render_category(cat),
            parse_mode="Markdown"
        )

    elif data == "balance":
        bal = get_balance(user_id)
        bot.send_message(
            call.message.chat.id,
            f"💰 *Ваш баланс:* {bal} ⭐\n\n"
            f"Пополнить можно через магазин.",
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "✅ Баланс показан")

    elif data == "refs":
        link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        bot.send_message(
            call.message.chat.id,
            f"👥 *Ваша реферальная ссылка:*\n`{link}`\n\n"
            f"За каждого нового пользователя вы получаете +0.5⭐",
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "✅ Ссылка отправлена")

    elif data == "stats":
        total_users = len(balances)
        total_orders = sum(len(orders.get(uid, [])) for uid in orders)
        bot.send_message(
            call.message.chat.id,
            f"📊 *Статистика:*\n"
            f"👤 Всего пользователей: {total_users}\n"
            f"📦 Всего заказов: {total_orders}",
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "✅ Статистика показана")

    elif data.startswith("buy_"):
        parts = data.split("_")
        if len(parts) >= 3:
            name = parts[1]
            price = int(parts[2])
            
            prices = [LabeledPrice(label=name, amount=price)]
            
            try:
                bot.send_invoice(
                    chat_id=call.message.chat.id,
                    title=f"🎁 {name}",
                    description=f"Покупка подарка {name} за {price} Stars",
                    invoice_payload=f"order_{user_id}_{name}_{price}_{int(time.time())}",
                    provider_token="",  # ПУСТАЯ СТРОКА
                    currency="XTR",      # TELEGRAM STARS
                    prices=prices,
                    start_parameter="gift_payment"
                )
                bot.answer_callback_query(call.id, "✅ Счёт создан")
            except Exception as e:
                bot.send_message(
                    call.message.chat.id,
                    f"❌ Ошибка: {str(e)}",
                    parse_mode="Markdown"
                )
                bot.answer_callback_query(call.id, "❌ Ошибка")

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    user_id = str(message.from_user.id)
    payment = message.successful_payment
    payload = payment.invoice_payload
    
    parts = payload.split("_")
    if len(parts) >= 4:
        item_name = parts[2]
        item_price = int(parts[3])
        
        # Сохраняем заказ
        if user_id not in orders:
            orders[user_id] = []
        orders[user_id].append({
            "order_id": parts[4] if len(parts) > 4 else str(int(time.time())),
            "item": item_name,
            "price": item_price,
            "status": "paid"
        })
        save_data(ORDERS_FILE, orders)
        
        # ============================================
        # ЗВЁЗДЫ УЖЕ НА ВАШЕМ АККАУНТЕ!
        # Бот только подтверждает оплату
        # ============================================
        bot.send_message(
            message.chat.id,
            f"✅ *Оплата успешна!*\n\n"
            f"🎁 Вы купили *{item_name}* за {item_price}⭐\n"
            f"📦 Заказ #{parts[4] if len(parts) > 4 else '—'}\n\n"
            f"⏳ Подарок придёт в течение 3 дней.\n"
            f"Спасибо за покупку!",
            parse_mode="Markdown"
        )
        
        # УВЕДОМЛЕНИЕ АДМИНИСТРАТОРУ (вам)
        ADMIN_ID = "СЮДА_ВАШ_TELEGRAM_ID"  # Узнайте через @userinfobot
        if ADMIN_ID != "СЮДА_ВАШ_TELEGRAM_ID":
            bot.send_message(
                ADMIN_ID,
                f"🔔 *Новый заказ!*\n"
                f"Пользователь: {user_id}\n"
                f"Товар: {item_name}\n"
                f"Сумма: {item_price}⭐\n"
                f"Статус: оплачен\n\n"
                f"💰 Звёзды уже на вашем балансе!",
                parse_mode="Markdown"
            )

if __name__ == "__main__":
    print("🟢 Бот PONCH1TA GIFTS (звёзды на ваш аккаунт) запущен!")
    print("🔄 Ожидание команд...")
    bot.infinity_polling()