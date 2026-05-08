from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from PIL import Image
import os

TOKEN = "8329558378:AAHsO-VRONdeDY3937r2ZCmFJmvFpSQMntc"

user_data = {}

A4_WIDTH = 2480
A4_HEIGHT = 3508


# =========================
# استلام الصورة
# =========================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    path = "input.jpg"

    await photo_file.download_to_drive(path)

    user_data[update.effective_chat.id] = {"image": path}

    keyboard = [
        [InlineKeyboardButton("📏 أفقي", callback_data="h")],
        [InlineKeyboardButton("📐 عمودي", callback_data="v")]
    ]

    await update.message.reply_text(
        "اختار نوع التقسيم:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# الأزرار
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id

    if chat_id not in user_data:
        await query.message.reply_text("ارسل صورة أولاً")
        return

    # حفظ النوع
    if query.data in ["h", "v"]:
        user_data[chat_id]["mode"] = query.data

        keyboard = [
            [InlineKeyboardButton("2 أجزاء", callback_data="2"),
             InlineKeyboardButton("3 أجزاء", callback_data="3")],
            [InlineKeyboardButton("4 أجزاء", callback_data="4"),
             InlineKeyboardButton("6 أجزاء", callback_data="6")]
        ]

        await query.message.reply_text(
            "اختار عدد الأجزاء:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # =========================
    # تنفيذ التقسيم
    # =========================
    parts_count = int(query.data)
    img_path = user_data[chat_id]["image"]
    mode = user_data[chat_id]["mode"]

    img = Image.open(img_path)

    parts = []

    # =========================
    # أفقي
    # =========================
    if mode == "h":
        width, height = img.size
        part_width = width // parts_count

        for i in range(parts_count):
            left = i * part_width
            right = (i + 1) * part_width if i < parts_count - 1 else width

            part = img.crop((left, 0, right, height))
            part = part.resize((A4_WIDTH, A4_HEIGHT), Image.LANCZOS)

            name = f"a4_h_{i+1}.png"
            part.save(name, "PNG", quality=100)
            parts.append(name)

    # =========================
    # عمودي
    # =========================
    else:
        width, height = img.size
        part_height = height // parts_count

        for i in range(parts_count):
            top = i * part_height
            bottom = (i + 1) * part_height if i < parts_count - 1 else height

            part = img.crop((0, top, width, bottom))
            part = part.resize((A4_WIDTH, A4_HEIGHT), Image.LANCZOS)

            name = f"a4_v_{i+1}.png"
            part.save(name, "PNG", quality=100)
            parts.append(name)

    # إرسال النتائج
    for file in parts:
        await query.message.reply_document(document=open(file, "rb"))

    # تنظيف
    os.remove(img_path)
    for file in parts:
        os.remove(file)

    user_data.pop(chat_id, None)


# =========================
# تشغيل البوت
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()