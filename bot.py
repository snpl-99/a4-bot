import io
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    CommandHandler
)

TOKEN = "8329558378:AAHsO-VRONdeDY3937r2ZCmFJmvFpSQMntc"

user_data = {}

A4_SIZE = (2480, 3508)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً!\n"
        "ارسل صورة وأنا أقسمها لك بسرعة ⚡️"
    )


# =========================
# استلام الصورة (أسرع طريقة)
# =========================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()

    bio = io.BytesIO()
    await file.download_to_memory(out=bio)
    bio.seek(0)

    user_data[update.effective_chat.id] = {"image": bio}

    keyboard = [
        [InlineKeyboardButton("📏 أفقي", callback_data="h"),
         InlineKeyboardButton("📐 عمودي", callback_data="v")]
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

    # اختيار الاتجاه
    if query.data in ["h", "v"]:
        user_data[chat_id]["mode"] = query.data

        keyboard = [
            [InlineKeyboardButton("2", callback_data="2"),
             InlineKeyboardButton("3", callback_data="3")],
            [InlineKeyboardButton("4", callback_data="4"),
             InlineKeyboardButton("6", callback_data="6")]
        ]

        await query.message.reply_text(
            "اختار عدد الأجزاء:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # تشغيل المعالجة بسرعة
    user_data[chat_id]["parts"] = int(query.data)

    context.application.create_task(process_image(chat_id, context))


# =========================
# المعالجة السريعة جداً
# =========================
async def process_image(chat_id, context):
    data = user_data.get(chat_id)
    if not data:
        return

    img = Image.open(data["image"]).convert("RGB")

    mode = data["mode"]
    parts = data["parts"]

    w, h = img.size

    results = []

    if mode == "h":
        step = w // parts

        for i in range(parts):
            left = i * step
            right = (i + 1) * step if i < parts - 1 else w

            crop = img.crop((left, 0, right, h))
            crop = crop.resize(A4_SIZE, Image.LANCZOS)

            bio = io.BytesIO()
            crop.save(bio, format="JPEG", quality=90, optimize=True)
            bio.seek(0)

            results.append(bio)

    else:
        step = h // parts

        for i in range(parts):
            top = i * step
            bottom = (i + 1) * step if i < parts - 1 else h

            crop = img.crop((0, top, w, bottom))
            crop = crop.resize(A4_SIZE, Image.LANCZOS)

            bio = io.BytesIO()
            crop.save(bio, format="JPEG", quality=90, optimize=True)
            bio.seek(0)

            results.append(bio)

    # إرسال سريع (batch send)
    media_group = []

    for i, b in enumerate(results):
        media_group.append(
            (b, f"part_{i+1}.jpg")
        )

    # إرسال واحد واحد لكن سريع جداً (بدون فتح/إغلاق ملفات)
    for file, name in media_group:
        await context.bot.send_document(
            chat_id=chat_id,
            document=file,
            filename=name
        )

    user_data.pop(chat_id, None)


# =========================
# تشغيل البوت
# =========================
app = ApplicationBuilder().token(TOKEN).build()
