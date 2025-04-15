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
BARBERS = ["Ира ✂️", "Аман 💈", "Олег 💬"]

# Варианты времени
TIME_OPTIONS = ["10:00", "11:00", "12:00", "13:00", "14:00"]

# Состояния пользователя
user_state = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"step": None}
    await update.message.reply_text(
        "Добро пожаловать в BarberBot 💈",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

# Обработка текстовых сообщений
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    state = user_state.get(user_id, {})
    step = state.get("step")

    if text == "💈 Записаться на стрижку":
        user_state[user_id] = {"step": "choose_barber"}
        await update.message.reply_text(
            "Выберите барбера:",
            reply_markup=ReplyKeyboardMarkup([[b] for b in BARBERS], resize_keyboard=True)
        )

    elif text in BARBERS and step == "choose_barber":
        user_state[user_id]["barber"] = text
        user_state[user_id]["step"] = "enter_name"
        await update.message.reply_text("Введите ваше имя:")

    elif step == "enter_name":
        user_state[user_id]["name"] = text
        user_state[user_id]["step"] = "choose_date"
        await update.message.reply_text("Введите дату записи (например, 15 апреля):")

    elif step == "choose_date":
        user_state[user_id]["date"] = text
        user_state[user_id]["step"] = "choose_time"
        await update.message.reply_text(
            "Выберите время:",
            reply_markup=ReplyKeyboardMarkup([[t] for t in TIME_OPTIONS], resize_keyboard=True)
        )

    elif text in TIME_OPTIONS and step == "choose_time":
        user_state[user_id]["time"] = text
        user_state[user_id]["step"] = "enter_phone"
        await update.message.reply_text("Введите ваш номер телефона (в формате 555 78 22 33):")

    elif step == "enter_phone":
        user_state[user_id]["phone"] = text
        d = user_state[user_id]
        await update.message.reply_text(
            f"✅ Запись подтверждена!\nБарбер: {d['barber']}\nИмя: {d['name']}\nДата: {d['date']}\nВремя: {d['time']}\nТелефон: {d['phone']}\n\nДо встречи! 💈",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        user_state[user_id] = {"step": None}  # сброс состояния

    elif text == "🧔 Наши барберы":
        await update.message.reply_text(
            "Наши мастера:\n1. Ира ✂️\n2. Аман 💈\n3. Олег 💬",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )

    elif text == "💼 Услуги и цены":
        await update.message.reply_text(
            "💇 Стрижка – 700\n🧔 Оформление бороды – 500\n💆 Полный комплекс – 1100",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )

    elif text == "📍 Адрес и контакты":
        await update.message.reply_text(
            "📍 ул. Барберская, 123\n📞 +996 (555) 23-45-67\n🕒 Режим работы: 10:00 – 20:00",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
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

