# ====== IMPORTS ======
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from flask import Flask
from threading import Thread

# ====== CONFIG ======
TOKEN = "8528159982:AAFynK9sNetbAYrBMfeHynShQN3-XPPcUpE"
LOG_CHAT_ID = -1003952290648
ALLOWED_CHAT_ID = -1003705469283

FORUM_LINK = "https://t.me/marino_rp"

ADMINS = [1633168964 , 1193085204]

# ====== DATABASE ======
balances = {}
jobs = {}
cars = {}

# ====== FLASK KEEP ALIVE ======
app = Flask('')

@app.route('/')
def home():
    return "alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ====== JOBS DATA ======
jobs_data = {
    "bus": {"name":"🚌 Водитель автобуса","desc":"Движение по маршруту","req":"медкнижка, кат Б,Д","salary":"5000"},
    "taxi": {"name":"🚕 Водитель такси","desc":"Доставка клиентов","req":"медкнижка, кат Б","salary":"2500"},
    "taxi2": {"name":"🚖 Такси личное авто","desc":"Доставка клиентов","req":"медкнижка, кат Б, личное авто","salary":"5000"},
    "courier": {"name":"📦 Курьер","desc":"Доставка товаров","req":"нет","salary":"1000"},
    "truck": {"name":"🚛 Водитель тягача","desc":"Грузоперевозки","req":"кат Б,С,Е","salary":"10000"},
    "electric": {"name":"⚡ Электрик","desc":"Ремонт электросетей","req":"проф образование","salary":"6000"},
    "janitor": {"name":"🧹 Дворник","desc":"Уборка улиц","req":"нет","salary":"1000"},
    "builder": {"name":"🏗 Строитель","desc":"Строительство зданий","req":"медкнижка","salary":"5000"},
    "doctor": {"name":"🚑 Врач","desc":"Лечение людей","req":"высшее образование","salary":"9000"},
    "police": {"name":"🚓 МВД","desc":"Служба полиции","req":"несудим","salary":"10000"},
    "mchs": {"name":"🚒 МЧС","desc":"Работа при ЧС","req":"медкнижка","salary":"10000"},
}

# ====== MENU ======
def main_menu():
    keyboard = [
        ["👤 Профиль"],
        ["📋 Информация о работах"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    await update.message.reply_text(
        "👋 Добро пожаловать в RP бота",
        reply_markup=main_menu()
    )

# ====== PROFILE ======
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    balances.setdefault(uid,0)
    jobs.setdefault(uid,"Без работы")
    cars.setdefault(uid,"Нет")

    text = (
        f"👤 Юз игрока: @{user.username}\n"
        f"💰 Баланс игрока: {balances[uid]} руб\n"
        f"💼 Работа игрока: {jobs[uid]}\n"
        f"🚗 Т/С игрока: {cars[uid]}"
    )
    await update.message.reply_text(text)

# ====== JOBS LIST ======
async def jobs_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for jid in jobs_data:
        keyboard.append([InlineKeyboardButton(jobs_data[jid]["name"], callback_data=f"job_{jid}")])

    await update.message.reply_text(
        "📋 Список работ:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====== JOB BUTTON ======
async def job_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    jid = query.data.replace("job_","")
    job = jobs_data[jid]

    text = (
        f"💼 {job['name']}\n\n"
        f"📋 Обязаности:\n{job['desc']}\n\n"
        f"📌 Требования:\n{job['req']}\n\n"
        f"💰 Зарплата:\n{job['salary']} руб\n\n"
        f"📎 Как трудоустроиться:\n{FORUM_LINK}"
    )

    await query.edit_message_text(text)

# ====== BUTTONS ======
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "👤 Профиль":
        await profile(update, context)

    elif update.message.text == "📋 Информация о работах":
        await jobs_info(update, context)

# ====== PAY ======
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = str(update.effective_user.id)

    if not update.message.reply_to_message:
        return await update.message.reply_text("Ответь на сообщение игрока")

    target = str(update.message.reply_to_message.from_user.id)

    amount = int(context.args[0])

    balances.setdefault(sender,0)
    balances.setdefault(target,0)

    if balances[sender] < amount:
        return await update.message.reply_text("Недостаточно средств")

    balances[sender] -= amount
    balances[target] += amount

    await update.message.reply_text("Перевод выполнен")

    await context.bot.send_message(
        chat_id=LOG_CHAT_ID,
        text=f"💸 PAY\n{sender} -> {target}\n{amount} руб"
    )

# ====== ADD ======
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    if not update.message.reply_to_message:
        return

    uid = str(update.message.reply_to_message.from_user.id)
    amount = int(context.args[0])

    balances.setdefault(uid,0)
    balances[uid] += amount

    await update.message.reply_text("Баланс изменен")

# ====== TOP ======
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(balances.items(), key=lambda x:x[1], reverse=True)[:10]

    text = "🏆 ТОП БАЛАНСОВ\n"
    for uid, bal in sorted_users:
        text += f"{uid} — {bal} руб\n"

    await update.message.reply_text(text)

# ====== MAIN ======
def main():
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("top", top))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buttons))
    app.add_handler(CallbackQueryHandler(job_buttons, pattern="job_"))

    app.run_polling()

if __name__ == "__main__":
    main()
