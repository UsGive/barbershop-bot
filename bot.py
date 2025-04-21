# Новый код для Бот BarberBot на инлайн-кнопках

import os
import asyncpg
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Загрузка токенов
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Барберы
BARBERS = {
    "Ира": "media/ira.jpg",
    "Аман": "media/aman.jpg",
    "Олег": "media/oleg.jpg"
}

# Время
TIME_OPTIONS = ["10:00", "11:00", "12:00", "13:00", "14:00"]

# Состояние пользователя
user_state = {}

# Пул базы
db_pool = None

# Получение дат
def get_upcoming_dates(n_days=14):
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(n_days)]

# Инициализация базы
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

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"step": None}

    await update.message.reply_text(
        "Добро пожаловать в BarberBot 💈\n\nНажмите на кнопку, чтобы начать:",
        reply_markup=ReplyKeyboardMarkup([
            ["💈 Записаться на стрижку"],
            ["💼 Услуги и цены", "📍 Адрес и контакты"]
        ], resize_keyboard=True)
    )

# Обработка текстовых сообщений
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "💈 Записаться на стрижку":
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"barber:{name}")] for name in BARBERS.keys()
        ]
        await update.message.reply_text(
            "Выберите барбера:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif text == "💼 Услуги и цены":
        await update.message.reply_text(
            "💇 Стрижка – 700\n🧔 Оформление бороды – 500\n💆 Полный комплекс – 1100"
        )

    elif text == "📍 Адрес и контакты":
        await update.message.reply_text(
            "📍 ул. Барберская, 123\n📞 +996 (555) 23-45-67\n🕒 Режим работы: 10:00 – 20:00"
        )

# Получение доступного времени
async def get_available_times(barber, date):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT time FROM appointments WHERE barber = $1 AND date = $2
        """, barber, date)
    booked = {row['time'] for row in rows}
    return [time for time in TIME_OPTIONS if time not in booked]

# Обработка инлайн кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("barber:"):
        barber = data.split(":")[1]
        user_state[user_id] = {"barber": barber, "step": "choose_date"}

        dates = get_upcoming_dates()
        keyboard = [[InlineKeyboardButton(date, callback_data=f"date:{date}")] for date in dates]

        await query.message.edit_text(
            f"Вы выбрали барбера: {barber}\nВыберите дату:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("date:"):
        date = data.split(":")[1]
        user_state[user_id]["date"] = date
        user_state[user_id]["step"] = "choose_time"

        available_times = await get_available_times(user_state[user_id]["barber"], date)
        if not available_times:
            await query.message.edit_text("❗ На эту дату нет свободного времени. Нажмите /start, чтобы выбрать другую дату.")
            return

        keyboard = [[InlineKeyboardButton(time, callback_data=f"time:{time}")] for time in available_times]
        await query.message.edit_text(
            f"Вы выбрали дату: {date}\nТеперь выберите время:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("time:"):
        time = data.split(":")[1]
        user_state[user_id]["time"] = time
        user_state[user_id]["step"] = "type_phone"

        await query.message.edit_text(
            f"Вы выбрали время: {time}\nВведите ваш номер телефона (формат 555 888888):"
        )

# Обработка ввода телефона и сохранение записи
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if user_id not in user_state:
        return

    step = user_state[user_id].get("step")
    if step == "type_phone":
        if text.replace(" ", "").isdigit() and len(text.replace(" ", "")) == 9:
            user_state[user_id]["phone"] = text
            d = user_state[user_id]

            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO appointments (user_id, barber, name, date, time, phone)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, user_id, d["barber"], update.effective_user.first_name, d["date"], d["time"], d["phone"])

            await update.message.reply_text(
                f"✅ Запись подтверждена!\nБарбер: {d['barber']}\nДата: {d['date']}\nВремя: {d['time']}\nТелефон: {d['phone']}\n\nСпасибо! 💈",
                reply_markup=ReplyKeyboardMarkup([
                    ["💈 Записаться на стрижку"],
                    ["💼 Услуги и цены", "📍 Адрес и контакты"]
                ], resize_keyboard=True)
            )
            user_state.pop(user_id)
        else:
            await update.message.reply_text("❗ Неверный формат номера. Пожалуйста, введите номер в формате 555 888888.")

# Основная функция
async def on_startup(app):
    await init_db()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
