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
    await update.message.reply_text("Group ကို စာရင်းသွင်းပြီးပါပြီ။")
  elif chat.type == "private":
    await update.message.reply_text("🤖 Bot အဆင်သင့်ဖြစ်ပါပြီ။")


async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if message and message.chat:
    if message.chat.type in ["group", "supergroup"]:
      allowed_chats.add(message.chat.id)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  if user_id != OWNER_ID:
    await update.message.reply_text("❌ Owner သာ အသုံးပြုနိုင်ပါသည်။")
    return

  ad_message = " ".join(context.args)
  if not ad_message and not update.message.reply_to_message:
    await update.message.reply_text("⚠️ ကြော်ငြာစာကို ရေးပါ သို့မဟုတ် Reply လုပ်ပါ။")
    return

  if update.message.reply_to_message:
    ad_message = (
        update.message.reply_to_message.text
        or update.message.reply_to_message.caption
        or ""
    )

  if not allowed_chats:
    await update.message.reply_text("⚠️ Group များ မတွေ့ရသေးပါ။")
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

  await update.message.reply_text(f"📢 ပို့ပြီးပါပြီ - အောင်မြင်: {success_count}")


async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message:
    return

  print("Mute command triggered!")  # Railway logs တွင် ပေါ်လာမည်

  if message.chat.type not in ["group", "supergroup"]:
    await message.reply_text("❌ Group ထဲတွင်သာ သုံးပါ။")
    return

  if not message.reply_to_message:
    await message.reply_text("⚠️ Mute လုပ်လိုသူ၏ စာကို Reply လုပ်ပြီး /mute ပါ။")
    return

  user_to_mute = message.reply_to_message.from_user
  if not user_to_mute:
    await message.reply_text("⚠️ ဤသူ၏ အချက်အလက်ကို ယူ၍မရပါ။")
    return

  try:
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )
    await context.bot.restrict_chat_member(
        chat_id=message.chat.id, user_id=user_to_mute.id, permissions=permissions
    )
    await message.reply_text(f"🔇 {user_to_mute.first_name} ကို Mute လုပ်လိုက်ပါပြီ။")
  except Exception as e:
    print(f"Mute Error: {e}")
    await message.reply_text(f"⚠️ Mute မလုပ်နိုင်ပါ Error: {e}")


async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message:
    return

  if message.chat.type not in ["group", "supergroup"]:
    await message.reply_text("❌ Group ထဲတွင်သာ သုံးပါ။")
    return

  if not message.reply_to_message:
    await message.reply_text(
        "⚠️ Unmute လုပ်လိုသူ၏ စာကို Reply လုပ်ပြီး /unmute ပါ။"
    )
    return

  user_to_unmute = message.reply_to_message.from_user
  if not user_to_unmute:
    await message.reply_text("⚠️ ဤသူ၏ အချက်အလက်ကို ယူ၍မရပါ။")
    return

  try:
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    await context.bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=user_to_unmute.id,
        permissions=permissions,
    )
    await message.reply_text(
        f"🔊 {user_to_unmute.first_name} ကို Unmute လုပ်ပေးလိုက်ပါပြီ။"
    )
  except Exception as e:
    print(f"Unmute Error: {e}")
    await message.reply_text(f"⚠️ Unmute မလုပ်နိုင်ပါ Error: {e}")


def main():
  app = ApplicationBuilder().token(TOKEN).build()

  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("broadcast", broadcast))
  app.add_handler(CommandHandler("mute", mute_user))
  app.add_handler(CommandHandler("unmute", unmute_user))
  app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), track_chats))

  print("Bot is running...")
  # drop_pending_updates=True ထည့်သွင်းထားသဖြင့် Webhook အဟောင်းများ ကင်းစင်ပြီး Command များကို တန်းဖမ်းမည်
  app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
  main()
    
