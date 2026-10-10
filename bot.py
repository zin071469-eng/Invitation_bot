import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bot Token နှင့် Owner ID
TOKEN = "8957681020:AAFLOZeDjmMRM4xDdZq7OLsqTWONmCx9pow"
OWNER_ID = 8062359539

# Group ID များကို သိမ်းဆည်းရန် Set တစ်ခု
allowed_chats = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        allowed_chats.add(chat.id)
        await update.message.reply_text("ဒီ Group ကို ကြော်ငြာစာရင်းထဲ အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။")
    elif chat.type == "private":
        await update.message.reply_text("မင်္ဂလာပါ၊ ဒါက ကြော်ငြာ Bot ဖြစ်ပါတယ်။")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your User ID: {user_id}\nCurrent Chat ID: {chat_id}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Owner ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    if user_id != OWNER_ID:
        await update.message.reply_text("ဒီခွင့်ပြုချက်ကို Owner သာ အသုံးပြုနိုင်ပါတယ်။")
        return

    # ပို့မယ့် ကြော်ငြာစာသား
    ad_message = " ".join(context.args)
    if not ad_message:
        await update.message.reply_text("ကျေးဇူးပြု၍ ကြော်ငြာစာသား ထည့်သွင်းပါ။ ဥပမာ: /broadcast သင့်ကြော်ငြာစာ")
        return

    if not allowed_chats:
        await update.message.reply_text("ကြော်ငြာပို့ရန် Group များ သိုလှောင်ထားခြင်း မရှိသေးပါ။ (Bot ကို Group ထဲသို့ ထည့်ပြီး /start ပို့ခိုင်းပါ)")
        return

    success_count = 0
    fail_count = 0
    
    for chat_id in allowed_chats:
        try:
            await context.bot.send_message(chat_id=chat_id, text=ad_message)
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Error sending to {chat_id}: {e}")

    await update.message.reply_text(f"ကြော်ငြာပို့ပြီးပါပြီ။\n- အောင်မြင်သည်: {success_count} ခု\n- မအောင်မြင်ပါ: {fail_count} ခု")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", myid))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

