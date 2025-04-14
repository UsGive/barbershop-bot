import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler, CallbackQueryHandler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Состояния для формы записи
CHOOSING_BARBER, TYPING_NAME, TYPING_PHONE, CHOOSING_DATE, CHOOSING_TIME = range(5)

# Главное меню
MAIN_MENU = [
    [KeyboardButton("💈 Записаться")],
    [KeyboardButton("🧔 Наши барберы")],
    [KeyboardButton("💼 Услуги и цены")],
    [KeyboardButton("📍 Контакты")]
]

# Доступные временные слоты
TIME_SLOTS = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]

# Барберы и их профили
BARBERS = {
    "Ира": {
        "photo": "ira.jpg",
        "profile": "✂️ Ира — специалист по классическим мужским и женским стрижкам. 5 лет опыта, внимательная к деталям и вежливая."
    },
    "Аман": {
        "photo": "aman.jpg",
        "profile": "💈 Аман — мастер фейдов и современных укладок. 4 года в профессии, стильный и профессиональный."
    },
    "Олег": {
        "photo": "oleg.jpg",
        "profile": "🧔 Олег — эксперт по уходу за бородой и коротким стрижкам. Более 6 лет опыта. Работает быстро и качественно."
    }
}

# Начало работы
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в BarberBot 💈",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

# Обработка главного меню
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🧔 Наши барберы":
        keyboard = [[KeyboardButton(name)] for name in BARBERS.keys()]
        await update.message.reply_text("Выберите барбера:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    elif text in BARBERS:
        barber = BARBERS[text]
        with open(f"{barber['photo']}", "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=barber["profile"])
    elif text == "💼 Услуги и цены":
        await update.message.reply_text("💇 Стрижка – 700\n🧔 Оформление бороды – 500\n💆 Полный комплекс – 1100")
    elif text == "📍 Контакты":
        await update.message.reply_text("📍 ул. Барберская, 123\n📞 +996 (555) 23-45-67\n🕒 Режим работы: 10:00 – 20:00")
    elif text == "💈 Записаться":
        keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in BARBERS.keys()]
        await update.message.reply_text("Выберите барбера:", reply_markup=InlineKeyboardMarkup(keyboard))
        return CHOOSING_BARBER

# Начало записи — выбор барбера
async def choose_barber_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['barber'] = query.data
    await query.message.reply_text("Введите ваше имя:")
    return TYPING_NAME

# Имя клиента
async def type_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите ваш номер телефона (в формате 555 99 99 99):")
    return TYPING_PHONE

# Телефон клиента
async def type_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Выберите дату (например, 15 апреля):")
    return CHOOSING_DATE

# Дата
async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    keyboard = [[KeyboardButton(time)] for time in TIME_SLOTS]
    await update.message.reply_text("Выберите время:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSING_TIME

# Время и финальное подтверждение
async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    d = context.user_data
    await update.message.reply_text(
        f"✅ Запись подтверждена!\nБарбер: {d['barber']}\nИмя: {d['name']}\nТелефон: {d['phone']}\nДата: {d['date']}\nВремя: {d['time']}\n\nСпасибо, ждем вас в нашем барбершопе! 💈",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )
    return ConversationHandler.END

# Завершение диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запись отменена.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
    return ConversationHandler.END

# Главный запуск
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💈 Записаться$"), handle_menu)],
        states={
            CHOOSING_BARBER: [CallbackQueryHandler(choose_barber_callback)],
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_name)],
            TYPING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_phone)],
            CHOOSING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_date)],
            CHOOSING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.run_polling()

if __name__ == '__main__':
    main()

