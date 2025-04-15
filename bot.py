import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Загрузка токена из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Главное меню
MAIN_MENU = [
    [KeyboardButton("💈 Записаться на стрижку")],
    [KeyboardButton("🧔 Наши барберы")],
    [KeyboardButton("💼 Услуги и цены")],
    [KeyboardButton("📍 Адрес и контакты")]
]

# Варианты барберов и профили
BARBERS = {
    "Ира ✂️": {
        "photo": "ira.jpg",
        "video": "video/ira.mp4",
        "profile": "✂️ Ира — специалист по классическим мужским и женским стрижкам. 5 лет опыта, внимательная к деталям и вежливая."
    },
    "Аман 💈": {
        "photo": "aman.jpg",
        "video": "video/aman.mp4",
        "profile": "💈 Аман — мастер фейдов и современных укладок. 4 года в профессии, стильный и профессиональный."
    },
    "Олег 💬": {
        "photo": "oleg.jpg",
        "video": "video/oleg.mp4",
        "profile": "🧔 Олег — эксперт по уходу за бородой и коротким стрижкам. Более 6 лет опыта. Работает быстро и качественно."
    }
}

# Варианты времени
TIME_OPTIONS = ["10:00", "11:00", "12:00", "13:00", "14:00"]

# Состояния пользователя
user_state = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        user_state[user_id] = {}
    await update.message.reply_text(
        "Добро пожаловать в BarberBot 💈",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

# Обработка текстовых сообщений
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if user_id not in user_state:
        user_state[user_id] = {}

    step = user_state[user_id].get("step")

    if text == "💈 Записаться на стрижку":
        user_state[user_id] = {"step": "name"}
        await update.message.reply_text("Пожалуйста, введите ваше имя:")

    elif step == "name":
        user_state[user_id]["name"] = text
        user_state[user_id]["step"] = "date"
        await update.message.reply_text("Укажите дату (например, 15 апреля):")

    elif step == "date":
        user_state[user_id]["date"] = text
        user_state[user_id]["step"] = "barber"
        await update.message.reply_text(
            "Выберите барбера:",
            reply_markup=ReplyKeyboardMarkup([[b] for b in BARBERS], resize_keyboard=True)
        )

    elif text in BARBERS and step == "barber":
        user_state[user_id]["barber"] = text
        user_state[user_id]["step"] = "time"
        await update.message.reply_text(
            "Выберите время:",
            reply_markup=ReplyKeyboardMarkup([[t] for t in TIME_OPTIONS], resize_keyboard=True)
        )

    elif text in TIME_OPTIONS and step == "time":
        user_state[user_id]["time"] = text
        d = user_state[user_id]
        await update.message.reply_text(
            f"✅ Запись подтверждена!\nИмя: {d['name']}\nДата: {d['date']}\nБарбер: {d['barber']}\nВремя: {d['time']}\nДо встречи! 💈",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        user_state[user_id] = {}  # сброс

    elif text == "🧔 Наши барберы":
        await update.message.reply_text(
            "Выберите барбера:",
            reply_markup=ReplyKeyboardMarkup([[b] for b in BARBERS], resize_keyboard=True)
        )
        user_state[user_id]["step"] = "show_barber"

    elif text in BARBERS and user_state[user_id].get("step") == "show_barber":
        barber = BARBERS[text]
        with open(barber["photo"], "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=barber["profile"])
        with open(barber["video"], "rb") as video:
            await update.message.reply_video(video=video)
        user_state[user_id]["step"] = None

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
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menu))
    app.run_polling()

if __name__ == "__main__":
    main()

