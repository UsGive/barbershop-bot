import os
import asyncpg
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Загрузка токена из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Главное меню
MAIN_MENU = [
    [KeyboardButton("💈 Записаться на стрижку")],
    [KeyboardButton("🧔 Наши барберы")],
    [KeyboardButton("💼 Услуги и цены")],
    [KeyboardButton("📍 Адрес и контакты")]
]
# Варианты барберов и их профили
BARBERS = {
    "Ира": {
        "photo": "media/ira.jpg",
        "video": "media/ira.mp4",
        "description": "✂️ Ира — специалист по классическим мужским и женским стрижкам. 5 лет опыта, внимательная к деталям и вежливая."
    },
    "Аман": {
        "photo": "media/aman.jpg",
        "video": "media/aman.mp4",
        "description": "💈 Аман — мастер фейдов и современных укладок. 4 года в профессии, стильный и профессиональный."
    },
    "Олег": {
        "photo": "media/oleg.jpg",
        "video": "media/oleg.mp4",
        "description": "🧔 Олег — эксперт по уходу за бородой и коротким стрижкам. Более 6 лет опыта. Работает быстро и качественно."
    }
}
# Варианты времени
TIME_OPTIONS = ["10:00", "11:00", "12:00", "13:00", "14:00"]

# Состояния пользователя
user_state = {}

# ID администраторов
ADMIN_IDS = [817664298]  # <-- сюда вставь свой Telegram user_id

# Пул подключений к базе данных
db_pool = None

# Функция для генерации списка ближайших 14 дней
def get_upcoming_dates(n_days=14):
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(n_days)]

# Инициализация базы данных
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
# Получение доступного времени для барбера на дату
async def get_available_times(barber, date):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT time FROM appointments
            WHERE barber = $1 AND date = $2
        """, barber, date)
    booked_times = {row['time'] for row in rows}
    available_times = [time for time in TIME_OPTIONS if time not in booked_times]
    return available_times

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"booking": None, "step": None}
    await update.message.reply_text(
        "Добро пожаловать в BarberBot 💈",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

# Обработка текстовых сообщений
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "💈 Записаться на стрижку":
        user_state[user_id] = {"step": "choose_barber"}
        await update.message.reply_text(
            "Выберите барбера:",
            reply_markup=ReplyKeyboardMarkup([[b] for b in BARBERS.keys()], resize_keyboard=True)
        )

    elif text in BARBERS and user_state.get(user_id, {}).get("step") == "choose_barber":
        user_state[user_id]["barber"] = text
        user_state[user_id]["step"] = "type_name"
        await update.message.reply_text(
            "Введите ваше имя:",
            reply_markup=ReplyKeyboardRemove()
        )

    elif user_state.get(user_id, {}).get("step") == "type_name":
        user_state[user_id]["name"] = text
        user_state[user_id]["step"] = "type_date"
        dates = get_upcoming_dates()
        await update.message.reply_text(
            "Выберите дату записи:",
            reply_markup=ReplyKeyboardMarkup([[d] for d in dates], resize_keyboard=True)
        )


    elif user_state.get(user_id, {}).get("step") == "type_date":

        user_state[user_id]["date"] = text

        user_state[user_id]["step"] = "choose_time"

        available_times = await get_available_times(user_state[user_id]["barber"], text)

        if not available_times:

            await update.message.reply_text(
                "❗ На эту дату уже нет свободного времени. Пожалуйста, выберите другую дату.")

            dates = get_upcoming_dates()

            await update.message.reply_text(

                "Выберите дату записи:",

                reply_markup=ReplyKeyboardMarkup([[d] for d in dates], resize_keyboard=True)

            )

        else:

            await update.message.reply_text(

                "Выберите время:",

                reply_markup=ReplyKeyboardMarkup([[t] for t in available_times], resize_keyboard=True)

            )


    elif user_state.get(user_id, {}).get("step") == "choose_time":

        available_times = await get_available_times(user_state[user_id]["barber"], user_state[user_id]["date"])

        if text in available_times:

            user_state[user_id]["time"] = text

            user_state[user_id]["step"] = "type_phone"

            await update.message.reply_text(

                "Введите ваш номер телефона (в формате 555 888888):",

                reply_markup=ReplyKeyboardRemove()

            )

        else:

            if available_times:

                await update.message.reply_text(

                    "❗ Это время уже занято. Пожалуйста, выберите другое:",

                    reply_markup=ReplyKeyboardMarkup([[t] for t in available_times], resize_keyboard=True)

                )

            else:

                await update.message.reply_text(

                    "❗ На эту дату нет свободного времени. Пожалуйста, выберите другую дату."

                )

                dates = get_upcoming_dates()

                await update.message.reply_text(

                    "Выберите дату записи:",

                    reply_markup=ReplyKeyboardMarkup([[d] for d in dates], resize_keyboard=True)

                )

    elif user_state.get(user_id, {}).get("step") == "type_phone":
        phone_parts = text.split()
        if len(phone_parts) == 2 and all(part.isdigit() for part in phone_parts) and len(phone_parts[0]) == 3 and len(phone_parts[1]) == 6:
            user_state[user_id]["phone"] = text
            d = user_state[user_id]
            await update.message.reply_text(
                f"✅ Запись подтверждена!\nБарбер: {d['barber']}\nИмя: {d['name']}\nДата: {d['date']}\nВремя: {d['time']}\nТелефон: {d['phone']}\n\nДо встречи! 💈",
                reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
            )
            # Сохраняем запись в базу данных
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO appointments (user_id, barber, name, date, time, phone)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, user_id, d['barber'], d['name'], d['date'], d['time'], d['phone'])
            user_state[user_id] = {"step": None}
        else:
            await update.message.reply_text(
                "Пожалуйста, введите номер в правильном формате (555 888888):"
            )

    elif text == "🧔 Наши барберы":
        await update.message.reply_text(
            "Выберите барбера:",
            reply_markup=ReplyKeyboardMarkup([[name] for name in BARBERS.keys()] + [["⬅️ Вернуться в меню"]], resize_keyboard=True)
        )

    elif text in BARBERS:
        barber = BARBERS[text]
        try:
            with open(barber["photo"], "rb") as photo_file:
                await update.message.reply_photo(photo=photo_file, caption=barber["description"])
            with open(barber["video"], "rb") as video_file:
                await update.message.reply_video(video=video_file)
        except Exception as e:
            await update.message.reply_text(f"Ошибка при загрузке медиа: {e}")
        await update.message.reply_text(
            "⬅️ Вернуться в меню",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )

    elif text == "⬅️ Вернуться в меню":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )

    elif text == "💼 Услуги и цены":
        await update.message.reply_text(
            "💇 Стрижка – 700\n🧔 Оформление бороды – 500\n💆 Полный комплекс – 1100"
        )

    elif text == "📍 Адрес и контакты":
        await update.message.reply_text(
            "📍 ул. Барберская, 123\n📞 +996 (555) 23-45-67\n🕒 Режим работы: 10:00 – 20:00"
        )

    else:
        await update.message.reply_text(
            "Пожалуйста, выберите вариант из меню.",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к админ-панели.")
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
        await update.message.reply_text("Записей на ближайшие 14 дней нет.")
    else:
        message = "📋 Записи на ближайшие 14 дней:\n\n"
        for row in rows:
            message += (
                f"👤 Имя: {row['name']}\n"
                f"💈 Барбер: {row['barber']}\n"
                f"📅 Дата: {row['date']}\n"
                f"⏰ Время: {row['time']}\n"
                f"📞 Телефон: {row['phone']}\n\n"
            )
        await update.message.reply_text(message)

# Запуск бота
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
