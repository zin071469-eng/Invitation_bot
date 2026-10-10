import logging
import os
from telegram import ChatPermissions, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

allowed_chats = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  chat = update.effective_chat
  if chat.type in ["group", "supergroup"]:
    allowed_chats.add(chat.id)
    await update.message.reply_text(
        "ဒီ Group ကို ကြော်ငြာစာရင်းထဲသို့ အောင်မြင်စွာ ထည့်သွင်းပြီးပြီ။"
    )
  elif chat.type == "private":
    await update.message.reply_text(
        "🤖 မင်္ဂလာပါ၊ ဒါက Admin နှင့် ကြော်ငြာ Bot ဖြစ်ပါသည်။"
    )


# ကြော်ငြာလွှင့်ခြင်း (Broadcast) - Owner သာ သုံးနိုင်သည်
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  if user_id != OWNER_ID:
    await update.message.reply_text("❌ ဤအမိန့်ကို Owner သာ အသုံးပြုနိုင်ပါသည်။")
    return

  ad_message = " ".join(context.args)
  if not ad_message and not update.message.reply_to_message:
    await update.message.reply_text(
        "⚠️ ကျေးဇူးပြု၍ ကြော်ငြာစာကို တွဲ၍ ရေးပါ (ဥပမာ: /broadcast မင်္ဂလာပါ)"
    )
    return

  if update.message.reply_to_message:
    ad_message = (
        update.message.reply_to_message.text
        or update.message.reply_to_message.caption
        or ""
    )

  if not allowed_chats:
    await update.message.reply_text(
        "⚠️ ကြော်ငြာမည့် Group များ မတွေ့ရသေးပါ။ (Bot ကို Group ထဲသို့ ထည့်ပြီး"
        " /start ခိုင်းပါ)"
    )
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

  await update.message.reply_text(
      f"📢 ကြော်ငြာပို့ပြီးပါပြီ-\n- အောင်မြင်သည်: {success_count}\n- ကျရှုံးသည်:"
      f" {fail_count}"
  )


# Admin ဟုတ်မဟုတ် စစ်ဆေးရန်
async def is_admin(chat, user_id):
  try:
    member = await chat.get_member(user_id)
    return member.status in ["creator", "administrator"]
  except:
    return False


# Anti-Link (လင့်ခ်စစ်ဆေးပြီး ဖျက်ခြင်း)
async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message or not message.chat:
    return
  if message.chat.type not in ["group", "supergroup"]:
    return

  text = message.text or message.caption or ""
  has_link = False

  if message.entities:
    for entity in message.entities:
      if entity.type in ["url", "text_link", "mention"]:
        has_link = True

  if (
      has_link
      or "http://" in text
      or "https://" in text
      or "t.me/" in text
      or "www." in text
  ):
    # Admin ဖြစ်ပါက မဖျက်ပါ
    if await is_admin(message.chat, message.from_user.id):
      return

    try:
      await message.delete()
      await message.reply_text(
          f"⚠️ @{message.from_user.username or message.from_user.first_name},"
          " ဤဂရုတွင် လင့်ခ်တင်ခွင့်မရှိပါ!"
      )
    except Exception as e:
      print(f"Error deleting link: {e}")


# /ban (အသုံးပြုသူကို ဂရုမှထုတ်ပစ်ရန်)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message or message.chat.type not in ["group", "supergroup"]:
    return
  if not await is_admin(message.chat, message.from_user.id):
    await message.reply_text("❌ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
    return

  if message.reply_to_message:
    user = message.reply_to_message.from_user
    try:
      await message.chat.ban_member(user.id)
      await message.reply_text(f"🔨 {user.first_name} ကို ဂရုမှ Ban လိုက်ပါပြီ။")
    except Exception as e:
      await message.reply_text(f"Error: {e}")
  else:
    await message.reply_text("⚠️ Ban လိုသူ၏ မက်ဆေ့ခ်ျကို Reply လုပ်ပြီး /ban ဟု ရိုက်ပါ။")


# /unban (ပိတ်ပင်ထားမှုကို ပြန်ဖြည်ရန်)
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message or message.chat.type not in ["group", "supergroup"]:
    return
  if not await is_admin(message.chat, message.from_user.id):
    await message.reply_text("❌ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
    return

  if context.args:
    try:
      user_id = int(context.args[0])
      await message.chat.unban_member(user_id)
      await message.reply_text(f"🔓 User ID {user_id} ကို Unban လုပ်ပေးလိုက်ပါပြီ။")
    except Exception as e:
      await message.reply_text(f"Error: {e}")
  else:
    await message.reply_text("⚠️ ဥပမာ - `/unban 123456789` ဟု အသုံးပြုပါ။")


# /mute (စကားပြောခွင့်ပိတ်ရန်)
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message:
    return

  if message.chat.type not in ["group", "supergroup"]:
    await message.reply_text("❌ ဤအမိန့်ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
    return

  if not await is_admin(message.chat, message.from_user.id):
    await message.reply_text("❌ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
    return

  if not message.reply_to_message:
    await message.reply_text(
        "⚠️ Mute လုပ်လိုသူ၏ မက်ဆေ့ခ်ျကို Reply လုပ်ပြီး /mute ဟု ရိုက်ပါကွာ။"
    )
    return

  user = message.reply_to_message.from_user
  try:
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )
    await context.bot.restrict_chat_member(
        chat_id=message.chat.id, user_id=user.id, permissions=permissions
    )
    await message.reply_text(f"🔇 {user.first_name} ကို Mute လုပ်လိုက်ပါပြီကွာ။")
  except Exception as e:
    await message.reply_text(f"⚠️ Mute လုပ်၍မရပါ Error: {e}")


# /unmute (စကားပြောခွင့် ပြန်ဖွင့်ရန်)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message:
    return

  if message.chat.type not in ["group", "supergroup"]:
    await message.reply_text("❌ ဤအမိန့်ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
    return

  if not await is_admin(message.chat, message.from_user.id):
    await message.reply_text("❌ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
    return

  if not message.reply_to_message:
    await message.reply_text(
        "⚠️ Unmute လုပ်လိုသူ၏ မက်ဆေ့ခ်ျကို Reply လုပ်ပြီး /unmute ဟု ရိုက်ပါကွာ။"
    )
    return

  user = message.reply_to_message.from_user
  try:
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    await context.bot.restrict_chat_member(
        chat_id=message.chat.id, user_id=user.id, permissions=permissions
    )
    await message.reply_text(
        f"🔊 {user.first_name} ကို Unmute လုပ်ပေးလိုက်ပါပြီကွာ။"
    )
  except Exception as e:
    await message.reply_text(f"⚠️ Unmute လုပ်၍မရပါ Error: {e}")


def main():
  app = ApplicationBuilder().token(TOKEN).build()

  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("broadcast", broadcast))
  app.add_handler(CommandHandler("ban", ban_user))
  app.add_handler(CommandHandler("unban", unban_user))
  app.add_handler(CommandHandler("mute", mute_user))
  app.add_handler(CommandHandler("unmute", unmute_user))

  # လင့်ခ်စစ်ဆေးသည့် Handler
  app.add_handler(
      MessageHandler(
          filters.TEXT & (~filters.COMMAND), check_links
      )
  )

  print("Bot is running...")
  app.run_polling()


if __name__ == "__main__":
  main()
    
