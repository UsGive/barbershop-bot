import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Главное меню
MAIN_MENU = [
    [KeyboardButton("💈 Записаться на стрижку")],
    [KeyboardButton("🧔 Наши барберы")],
    [KeyboardButton("💼 Услуги и цены")],
    [KeyboardButton("📍 Адрес и контакты")]
]

# Барберы и данные
BARBERS = {
    "Ира": {
        "photo": "photos/ira.jpg",
        "video": "videos/ira.mp4",
        "desc": "✂️ Ира — специалист по классическим мужским и женским стрижкам. 5 лет опыта, внимательная к деталям и вежливая."
    },
    "Аман": {
        "photo": "photos/aman.jpg",
        "video": "videos/aman.mp4",
        "desc": "💈 Аман — мастер фейдов и современных укладок. 4 года в профессии, стильный и профессиональный."
    },
    "Олег": {
        "photo": "photos/oleg.jpg",
        "video": "videos/oleg.mp4",
        "desc": "🧔 Олег — эксперт по уходу за бородой и коротким стрижкам. Более 6 лет опыта. Работает быстро и качественно."
    }
}

# Варианты времени
TIME_OPTIONS = ["10:00", "11:00", "12:00", "13:00", "14:00"]

# Состояния
CHOOSE_BARBER, TYPING_NAME, TYPING_DATE, TYPING_TIME, TYPING_PHONE = range(5)

user_state = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в BarberBot 💈",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

# Главное меню
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "🧔 Наши барберы":
        keyboard = [[KeyboardButton(name)] for name in BARBERS.keys()]
        await update.message.reply_text("Выберите барбера:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif text in BARBERS:
        barber = BARBERS[text]
        with open(barber['photo'], 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=barber['desc'])
        with open(barber['video'], 'rb') as video:
            await update.message.reply_video(video=video)
        await update.message.reply_text("Вернуться в меню:", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

    elif text == "💼 Услуги и цены":
        await update.message.reply_text(
            "💇 Стрижка – 700\n🧔 Оформление бороды – 500\n💆 Полный комплекс – 1100"
        )

    elif text == "📍 Адрес и контакты":
        await update.message.reply_text(
            "📍 ул. Барберская, 123\n📞 +996 (555) 23-45-67\n🕒 Режим работы: 10:00 – 20:00"
        )

# Этапы записи
async def book_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton(name)] for name in BARBERS.keys()]
    await update.message.reply_text("Выберите барбера:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSE_BARBER

async def choose_barber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['barber'] = update.message.text
    await update.message.reply_text("Введите ваше имя:")
    return TYPING_NAME

async def type_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите дату записи (например, 15 апреля):")
    return TYPING_DATE

async def type_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    keyboard = [[KeyboardButton(t)] for t in TIME_OPTIONS]
    await update.message.reply_text("Выберите время:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return TYPING_TIME

async def type_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time = update.message.text
    if time not in TIME_OPTIONS:
        await update.message.reply_text("Пожалуйста, выберите время из списка.")
        return TYPING_TIME
    context.user_data['time'] = time
    await update.message.reply_text("Введите ваш номер телефона (в формате 555 78 22 33):")
    return TYPING_PHONE

async def type_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    if not phone.replace(" ", "").isdigit() or len(phone.replace(" ", "")) != 9:
        await update.message.reply_text("Пожалуйста, введите номер в правильном формате (555 78 22 33):")
        return TYPING_PHONE
    context.user_data['phone'] = phone

    d = context.user_data
    await update.message.reply_text(
        f"✅ Запись подтверждена!\nБарбер: {d['barber']}\nИмя: {d['name']}\nДата: {d['date']}\nВремя: {d['time']}\nТелефон: {d['phone']}\n\nДо встречи! 💈",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )
    return ConversationHandler.END

# Завершение
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запись отменена.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
    return ConversationHandler.END

# Основной запуск
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💈 Записаться на стрижку$"), book_start)],
        states={
            CHOOSE_BARBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_barber)],
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_name)],
            TYPING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_date)],
            TYPING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_time)],
            TYPING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    app.run_polling()

if __name__ == "__main__":
    main()