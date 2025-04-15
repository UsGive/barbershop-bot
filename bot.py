from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler, CallbackQueryHandler
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

CHOOSING_BARBER, TYPING_NAME, TYPING_PHONE, CHOOSING_DATE, CHOOSING_TIME = range(5)

MAIN_MENU = [
    [KeyboardButton("💈 Записаться на стрижку")],
    [KeyboardButton("🧔 Наши барберы")],
    [KeyboardButton("💼 Услуги и цены")],
    [KeyboardButton("📍 Адрес и контакты")]
]

BARBERS = {
    "Ира": {
        "photo": "photos/ira.jpg",
        "profile": "✂️ Ира — специалист по классическим мужским и женским стрижкам. 5 лет опыта, внимательная к деталям и вежливая.",
        "video": "videos/ira.mp4"
    },
    "Аман": {
        "photo": "photos/aman.jpg",
        "profile": "💈 Аман — мастер фейдов и современных укладок. 4 года в профессии, стильный и профессиональный.",
        "video": "videos/aman.mp4"
    },
    "Олег": {
        "photo": "photos/oleg.jpg",
        "profile": "🧔 Олег — эксперт по уходу за бородой и коротким стрижкам. Более 6 лет опыта. Работает быстро и качественно.",
        "video": "videos/oleg.mp4"
    }
}

user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"booking": None}
    await update.message.reply_text(
        "Добро пожаловать в BarberBot 💈",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "💈 Записаться на стрижку":
        user_state[user_id] = {"step": "choose_barber"}
        keyboard = [[KeyboardButton(name)] for name in BARBERS.keys()]
        await update.message.reply_text("Выберите барбера:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif text in BARBERS and user_state.get(user_id, {}).get("step") == "choose_barber":
        user_state[user_id]["barber"] = text
        user_state[user_id]["step"] = "type_name"
        await update.message.reply_text("Введите ваше имя:")

    elif user_state.get(user_id, {}).get("step") == "type_name":
        user_state[user_id]["name"] = text
        user_state[user_id]["step"] = "choose_date"
        await update.message.reply_text("Введите дату записи (например, 15 апреля):")

    elif user_state.get(user_id, {}).get("step") == "choose_date":
        user_state[user_id]["date"] = text
        user_state[user_id]["step"] = "choose_time"
        await update.message.reply_text("Выберите время:", reply_markup=ReplyKeyboardMarkup([[t] for t in ["10:00", "11:00", "12:00", "13:00", "14:00"]], resize_keyboard=True))

    elif user_state.get(user_id, {}).get("step") == "choose_time":
        user_state[user_id]["time"] = text
        user_state[user_id]["step"] = "type_phone"
        await update.message.reply_text("Введите ваш номер телефона (в формате 555 78 22 33):")

    elif user_state.get(user_id, {}).get("step") == "type_phone":
        user_state[user_id]["phone"] = text
        d = user_state[user_id]
        await update.message.reply_text(
            f"✅ Запись подтверждена!\nБарбер: {d['barber']}\nИмя: {d['name']}\nДата: {d['date']}\nВремя: {d['time']}\nТелефон: {d['phone']}\n\nДо встречи! 💈",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        user_state[user_id] = {}

    elif text == "🧔 Наши барберы":
        keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in BARBERS.keys()]
        await update.message.reply_text("Выберите барбера:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "💼 Услуги и цены":
        await update.message.reply_text("💇 Стрижка – 700\n🧔 Оформление бороды – 500\n💆 Полный комплекс – 1100")

    elif text == "📍 Адрес и контакты":
        await update.message.reply_text("📍 ул. Барберская, 123\n📞 +996 (555) 23-45-67\n🕒 Режим работы: 10:00 – 20:00")

    else:
        await update.message.reply_text("Пожалуйста, выберите вариант из меню.")

async def show_barber_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    barber_name = query.data
    barber = BARBERS.get(barber_name)
    if barber:
        with open(barber['photo'], "rb") as photo:
            await query.message.reply_photo(photo=photo)
        await query.message.reply_text(barber['profile'])
        with open(barber['video'], "rb") as vid:
            await query.message.reply_video(video=vid)
        await query.message.reply_text("Возврат в главное меню:", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

# Запуск бота

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_barber_profile))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.run_polling()

if __name__ == "__main__":
    main()

