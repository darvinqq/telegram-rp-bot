import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8528159982:AAFynK9sNetbAYrBMfeHynShQN3-XPPcUpE"
ADMINS = [1633168964 , 1193085204]
LOG_CHAT_ID = -1003488568426

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")
conn.commit()

def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    conn.commit()
    return 0

def update_balance(user_id, amount):
    get_balance(user_id)
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

def get_top():
    cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
    return cursor.fetchall()

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = get_balance(update.effective_user.id)
    await update.message.reply_text(f"💰 Баланс: {bal} руб.")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    bal = get_balance(user)

    top = get_top()
    place = "-"
    for i, (uid, _) in enumerate(top, 1):
        if uid == user:
            place = i
            break

    await update.message.reply_text(
        f"👤 Профиль\n🆔 {user}\n💰 {bal} руб.\n🏆 Место: {place}"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    user = update.message.reply_to_message.from_user.id
    amount = int(context.args[0])
    update_balance(user, amount)
    await update.message.reply_text(f"✅ +{amount} руб.")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    user = update.message.reply_to_message.from_user.id
    amount = int(context.args[0])
    update_balance(user, -amount)
    await update.message.reply_text(f"➖ {amount} руб.")

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id
    receiver = update.message.reply_to_message.from_user.id
    amount = int(context.args[0])

    if get_balance(sender) < amount:
        await update.message.reply_text("❌ нет денег")
        return

    update_balance(sender, -amount)
    update_balance(receiver, amount)

    await update.message.reply_text(f"💸 +{amount} руб")

    await context.bot.send_message(
        chat_id=LOG_CHAT_ID,
        text=f"🧾 Перевод\n{sender} → {receiver}\n{amount} руб"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_top()
    text = "🏆 ТОП:\n"
    for i, (uid, bal) in enumerate(data, 1):
        text += f"{i}. {uid} — {bal} руб\n"
    await update.message.reply_text(text)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("remove", remove))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(CommandHandler("top", top))

app.run_polling()
