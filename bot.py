import os
import asyncio
import asyncpg
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
# Генерация списка дат на ближайшие 14 дней (в формате "ДД ММММ", например "16 апреля")
DATE_OPTIONS = [
    (datetime.now() + timedelta(days=i)).strftime("%d %B")
    for i in range(14)
]
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
# Работа с базой данных
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            barber TEXT,
            name TEXT,
            date TEXT,
            time TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await conn.close()
async def save_booking(user_id, barber, name, date, time, phone):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        INSERT INTO bookings (user_id, barber, name, date, time, phone)
        VALUES ($1, $2, $3, $4, $5, $6)
    ''', user_id, barber, name, date, time, phone)
    await conn.close()
# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("START TRIGGERED")  # для логов Railway

    if update.message:
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
        await update.message.reply_text("Введите ваше имя:")

    elif user_state.get(user_id, {}).get("step") == "type_name":

        user_state[user_id]["name"] = text

        user_state[user_id]["step"] = "choose_date"

        await update.message.reply_text(

            "Выберите дату записи:",

            reply_markup=ReplyKeyboardMarkup(

                [DATE_OPTIONS[i:i + 2] for i in range(0, len(DATE_OPTIONS), 2)],

                resize_keyboard=True

            )

        )

    elif user_state.get(user_id, {}).get("step") == "choose_date":

        if text in DATE_OPTIONS:

            user_state[user_id]["date"] = text

            user_state[user_id]["step"] = "choose_time"

            await update.message.reply_text(

                "Выберите время:",

                reply_markup=ReplyKeyboardMarkup(

                    [TIME_OPTIONS[i:i + 2] for i in range(0, len(TIME_OPTIONS), 2)],

                    resize_keyboard=True

                )

            )

        else:

            await update.message.reply_text("Пожалуйста, выберите дату из предложенных вариантов.")

    elif text in TIME_OPTIONS and user_state.get(user_id, {}).get("step") == "choose_time":
        user_state[user_id]["time"] = text
        user_state[user_id]["step"] = "type_phone"
        await update.message.reply_text("Введите ваш номер телефона (в формате 555 78 22 33):")


    elif user_state.get(user_id, {}).get("step") == "type_phone":

        if len(text.split()) == 4 and all(part.isdigit() for part in text.split()):

            user_state[user_id]["phone"] = text

            d = user_state[user_id]

            confirmation_text = (

                f"✅ Запись подтверждена!\n"

                f"Барбер: {d['barber']}\n"

                f"Имя: {d['name']}\n"

                f"Дата: {d['date']}\n"

                f"Время: {d['time']}\n"

                f"Телефон: {d['phone']}\n\n"

                f"До встречи! 💈"

            )

            await update.message.reply_text(confirmation_text,
                                            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

            # Сохранение данных в PostgreSQL
            await save_booking(
                user_id=user_id,
                barber=d['barber'],
                name=d['name'],
                date=d['date'],
                time=d['time'],
                phone=d['phone']
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
        await update.message.reply_text("⬅️ Вернуться в меню", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

    elif text == "⬅️ Вернуться в меню":
        await update.message.reply_text("Главное меню:", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

    elif text == "💼 Услуги и цены":
        await update.message.reply_text(
            "💇 Стрижка – 700\n🧔 Оформление бороды – 500\n💆 Полный комплекс – 1100"
        )

    elif text == "📍 Адрес и контакты":
        await update.message.reply_text(
            "📍 ул. Барберская, 123\n📞 +996 (555) 23-45-67\n🕒 Режим работы: 10:00 – 20:00"
        )

    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из меню.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

# Запуск бота
def main():
    loop = asyncio.get_event_loop()

    # Запускаем init_db в loop
    loop.run_until_complete(init_db())
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu))

    # Запускаем бот (внутри его собственного цикла)
    app.run_polling()
