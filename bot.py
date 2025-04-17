import os
import asyncpg
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Главное меню
MAIN_MENU = [
    [KeyboardButton("\ud83d\udcbc \u0417\u0430\u043f\u0438\u0441\u0430\u0442\u044c\u0441\u044f \u043d\u0430 \u0441\u0442\u0440\u0438\u0436\u043a\u0443")],
    [KeyboardButton("\ud83e\uddc4 \u041d\u0430\u0448\u0438 \u0431\u0430\u0440\u0431\u0435\u0440\u044b")],
    [KeyboardButton("\ud83d\udcbc \u0423\u0441\u043b\u0443\u0433\u0438 \u0438 \u0446\u0435\u043d\u044b")],
    [KeyboardButton("\ud83d\udccd \u0410\u0434\u0440\u0435\u0441 \u0438 \u043a\u043e\u043d\u0442\u0430\u043a\u0442\u044b")]
]

# Барберы
BARBERS = {
    "\u0418\u0440\u0430": {
        "photo": "media/ira.jpg",
        "video": "media/ira.mp4",
        "description": "\u2702\ufe0f \u0418\u0440\u0430 \u2014 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442 \u043f\u043e \u043a\u043b\u0430\u0441\u0441\u0438\u0447\u0435\u0441\u043a\u0438\u043c \u0441\u0442\u0440\u0438\u0436\u043a\u0430\u043c."
    },
    "\u0410\u043c\u0430\u043d": {
        "photo": "media/aman.jpg",
        "video": "media/aman.mp4",
        "description": "\ud83d\udcbc \u0410\u043c\u0430\u043d \u2014 \u043c\u0430\u0441\u0442\u0435\u0440 \u0444\u0435\u0439\u0434\u043e\u0432 \u0438 \u0443\u043a\u043b\u0430\u0434\u043e\u043a."
    },
    "\u041e\u043b\u0435\u0433": {
        "photo": "media/oleg.jpg",
        "video": "media/oleg.mp4",
        "description": "\ud83e\uddc4 \u041e\u043b\u0435\u0433 \u2014 \u044d\u043a\u0441\u043f\u0435\u0440\u0442 \u043f\u043e \u0443\u0445\u043e\u0434\u0443 \u0437\u0430 \u0431\u043e\u0440\u043e\u0434\u043e\u0439."
    }
}

TIME_OPTIONS = ["10:00", "11:00", "12:00", "13:00", "14:00"]

user_state = {}

db_pool = None

# Администраторы
ADMIN_IDS = [123456789]  # ЗАМЕНИ 123456789 на свой настоящий Telegram ID

def get_upcoming_dates(n_days=14):
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(n_days)]

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            barber TEXT,
            name TEXT,
            date TEXT,
            time TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"booking": None, "step": None}
    await update.message.reply_text(
        "\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c \u0432 BarberBot \ud83d\udcbc",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "\ud83d\udcbc \u0417\u0430\u043f\u0438\u0441\u0430\u0442\u044c\u0441\u044f \u043d\u0430 \u0441\u0442\u0440\u0438\u0436\u043a\u0443":
        user_state[user_id] = {"step": "choose_barber"}
        await update.message.reply_text(
            "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0431\u0430\u0440\u0431\u0435\u0440\u0430:",
            reply_markup=ReplyKeyboardMarkup([[b] for b in BARBERS.keys()], resize_keyboard=True)
        )

    elif text in BARBERS and user_state.get(user_id, {}).get("step") == "choose_barber":
        user_state[user_id]["barber"] = text
        user_state[user_id]["step"] = "type_name"
        await update.message.reply_text("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0432\u0430\u0448\u0435 \u0438\u043c\u044f:", reply_markup=ReplyKeyboardRemove())

    elif user_state.get(user_id, {}).get("step") == "type_name":
        user_state[user_id]["name"] = text
        user_state[user_id]["step"] = "choose_date"
        dates = get_upcoming_dates()
        await update.message.reply_text(
            "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0430\u0442\u0443:",
            reply_markup=ReplyKeyboardMarkup([[d] for d in dates], resize_keyboard=True)
        )

    elif user_state.get(user_id, {}).get("step") == "choose_date":
        user_state[user_id]["date"] = text
        user_state[user_id]["step"] = "choose_time"
        await update.message.reply_text(
            "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0432\u0440\u0435\u043c\u044f:",
            reply_markup=ReplyKeyboardMarkup([[t] for t in TIME_OPTIONS], resize_keyboard=True)
        )

    elif text in TIME_OPTIONS and user_state.get(user_id, {}).get("step") == "choose_time":
        user_state[user_id]["time"] = text
        user_state[user_id]["step"] = "type_phone"
        await update.message.reply_text("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043b\u0435\u0444\u043e\u043d (555 888888):", reply_markup=ReplyKeyboardRemove())

    elif user_state.get(user_id, {}).get("step") == "type_phone":
        phone_parts = text.split()
        if len(phone_parts) == 2 and all(part.isdigit() for part in phone_parts) and len(phone_parts[0]) == 3 and len(phone_parts[1]) == 6:
            user_state[user_id]["phone"] = text
            d = user_state[user_id]
            await update.message.reply_text(
                f"\u2705 \u0417\u0430\u043f\u0438\u0441\u044c \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430!\n\n\u0411\u0430\u0440\u0431\u0435\u0440: {d['barber']}\n\u0418\u043c\u044f: {d['name']}\n\u0414\u0430\u0442\u0430: {d['date']}\n\u0412\u0440\u0435\u043c\u044f: {d['time']}\n\u0422\u0435\u043b\u0435\u0444\u043e\u043d: {d['phone']}\n\n\u0414\u043e \u0432\u0441\u0442\u0440\u0435\u0447\u0438! \ud83d\udcbc",
                reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
            )
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO appointments (user_id, barber, name, date, time, phone)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, user_id, d['barber'], d['name'], d['date'], d['time'], d['phone'])
            user_state[user_id] = {"step": None}
        else:
            await update.message.reply_text("\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442. \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0430\u043a: 555 888888")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("\u26d4\ufe0f \u0423 \u0432\u0430\u0441 \u043d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430 \u043a \u0430\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u0438.")
        return

    today = datetime.now().date()
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT barber, name, date, time, phone
            FROM appointments
            WHERE to_date(date, 'DD.MM.YYYY') BETWEEN $1 AND $2
            ORDER BY to_date(date, 'DD.MM.YYYY'), time
        """, today, today + timedelta(days=14))

    if not rows:
        await update.message.reply_text("\u0417\u0430\u043f\u0438\u0441\u0435\u0439 \u043d\u0435\u0442.")
    else:
        message = "\ud83d\udccb \u0417\u0430\u043f\u0438\u0441\u0438:\n\n"
        for row in rows:
            message += (
                f"\u0411\u0430\u0440\u0431\u0435\u0440: {row['barber']}\n"
                f"\u0418\u043c\u044f: {row['name']}\n"
                f"\u0414\u0430\u0442\u0430: {row['date']}\n"
                f"\u0412\u0440\u0435\u043c\u044f: {row['time']}\n"
                f"\u0422\u0435\u043b\u0435\u0444\u043e\u043d: {row['phone']}\n\n"
            )
        await update.message.reply_text(message)

async def on_startup(app):
    await init_db()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu))
    app.run_polling()

if __name__ == "__main__":
    main()
