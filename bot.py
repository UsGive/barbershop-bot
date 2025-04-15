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

# Варианты барберов
BARBERS = {
    "Ира": {
        "photo": "media/ira.jpg",
        "video": "media/ira.mp4",
        "desc": "✂️ Ира — специалист по классическим мужским и женским стрижкам. 5 лет опыта, внимательная к деталям и вежливая."
    },
    "Аман": {
        "photo": "media/aman.jpg",
        "video": "media/aman.mp4",
        "desc": "💈 Аман — мастер фейдов и современных укладок. 4 года в профессии, стильный и профессиональный."
    },
    "Олег": {
        "photo": "media/oleg.jpg",
        "video": "media/oleg.mp4",
        "desc": "🧔 Олег — эксперт по уходу за бородой и коротким стрижкам. Более 6 лет опыта. Работает быстро и качественно."
    }
}

# Варианты времени
TIME_OPTIONS = ["10:00", "11:00", "12:00", "13:00", "14:00"]

# Состояния пользователя
user_state = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"booking": None}
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
            reply_markup=ReplyKeyboardMarkup([[name] for name in BARBERS], resize_keyboard=True)
        )

    elif text in BARBERS and user_state.get(user_id, {}).get("step") == "choose_barber":
        user_state[user_id]["barber"] = text
        user_state[user_id]["step"] = "choose_time"
        await update.message.reply_text(
            "Выберите время:",
            reply_markup=ReplyKeyboardMarkup([[t] for t in TIME_OPTIONS], resize_keyboard=True)
        )

    elif text in TIME_OPTIONS and user_state.get(user_id, {}).get("step") == "choose_time":
        barber = user_state[user_id].get("barber")
        time = text
        await update.message.reply_text(
            f"✅ Запись подтверждена!\nБарбер: {barber}\nВремя: {time}\nДо встречи! 💈",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        user_state[user_id] = {}  # сброс

    elif text == "🧔 Наши барберы":
        keyboard = [[name] for name in BARBERS]
        await update.message.reply_text("Выберите барбера:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif text in BARBERS:
        barber = BARBERS[text]
        with open(barber["photo"], "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=barber["desc"])
        with open(barber["video"], "rb") as video:
            await update.message.reply_video(video=video)
        await update.message.reply_text("⬅️ Вернуться в меню", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

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

# Запуск бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.run_polling()

if __name__ == "__main__":
    main()
