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


async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if message and message.chat:
    if message.chat.type in ["group", "supergroup"]:
      allowed_chats.add(message.chat.id)


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
    await update.message.reply_text("⚠️ ကြော်ငြာမည့် Group များ မတွေ့ရသေးပါ။")
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


async def is_admin(chat, user_id):
  try:
    member = await chat.get_member(user_id)
    return member.status in ["creator", "administrator"]
  except Exception as e:
    print(f"Admin check error: {e}")
    return False


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
      or "t.me://" in text
      or "www." in text
  ):
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


# /mute (စကားပြောခွင့်ပိတ်ရန် - အသေးစိတ် Debug ဖော်ပြပေးရန်)
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message:
    return

  print("Mute command received!")  # Railway logs တွင် ပေါ်လာမည်

  if message.chat.type not in ["group", "supergroup"]:
    await message.reply_text("❌ ဤအမိန့်ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
    return

  # Admin ဟုတ်မဟုတ် စစ်ဆေးခြင်း
  admin_check = await is_admin(message.chat, message.from_user.id)
  if not admin_check:
    await message.reply_text("❌ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
    return

  if not message.reply_to_message:
    await message.reply_text(
        "⚠️ Mute လုပ်လိုသူ၏ မက်ဆေ့ခ်ျကို Reply လုပ်ပြီး /mute ဟု ရိုက်ပါ။"
    )
    return

  if not message.reply_to_message.from_user:
    await message.reply_text("⚠️ ဤအသုံးပြုသူ၏ အချက်အလက်ကို ယူ၍မရပါ။")
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
    await message.reply_text(f"🔇 {user.first_name} ကို Mute လုပ်လိုက်ပါပြီ။")
    print(f"Successfully muted user {user.id}")
  except Exception as e:
    print(f"Mute Error: {e}")
    await message.reply_text(f"⚠️ Mute မလုပ်နိုင်ပါ Error: {e}")


# /unmute (စကားပြောခွင့် ပြန်ဖွင့်ရန်)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message:
    return

  print("Unmute command received!")

  if message.chat.type not in ["group", "supergroup"]:
    await message.reply_text("❌ ဤအမိန့်ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
    return

  if not await is_admin(message.chat, message.from_user.id):
    await message.reply_text("❌ ဤအမိန့်ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
    return

  if not message.reply_to_message:
    await message.reply_text(
        "⚠️ Unmute လုပ်လိုသူ၏ မက်ဆေ့ခ်ျကို Reply လုပ်ပြီး /unmute ဟု ရိုက်ပါ။"
    )
    return

  if not message.reply_to_message.from_user:
    await message.reply_text("⚠️ ဤအသုံးပြုသူ၏ အချက်အလက်ကို ယူ၍မရပါ။")
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
    await message.reply_text(f"🔊 {user.first_name} ကို Unmute လုပ်ပေးလိုက်ပါပြီ။")
    print(f"Successfully unmuted user {user.id}")
  except Exception as e:
    print(f"Unmute Error: {e}")
    await message.reply_text(f"⚠️ Unmute မလုပ်နိုင်ပါ Error: {e}")


def main():
  app = ApplicationBuilder().token(TOKEN).build()

  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("broadcast", broadcast))
  app.add_handler(CommandHandler("mute", mute_user))
  app.add_handler(CommandHandler("unmute", unmute_user))

  app.add_handler(
      MessageHandler(
          filters.ALL & (~filters.COMMAND), track_chats
      )
  )
  app.add_handler(
      MessageHandler(
          filters.TEXT & (~filters.COMMAND), check_links
      )
  )

  print("Bot is running...")
  app.run_polling()


if __name__ == "__main__":
  main()
    
