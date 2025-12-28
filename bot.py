import os
import logging
from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI
import uvicorn
# from config import CHANNELS # Agar config.py dan foydalanishni xohlasangiz qoldiring

# 1. Konfiguratsiya (Configuration)
logging.basicConfig(level=logging.INFO)

# O'zgaruvchilarni Environment Variables (Railway) orqali o'qish
BOT_TOKEN = os.getenv("BOT_TOKEN") 
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv("PORT", 8000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL") 
WEBHOOK_PATH = f'/{BOT_TOKEN}' # Xavfsiz webhook yo'li

# Bot va Dispatcher obyektlari
if not BOT_TOKEN:
    logging.critical("BOT_TOKEN Railway Variables'da o'rnatilmagan!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# 2. Telegram Handler (Asosiy Logika)
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    await message.reply("Assalomu alaykum! Bot muvaffaqiyatli ishga tushdi.")

# >>> BU YERGA SIZNING ASOSIY YUKLAB OLISH (DOWNLOAD) LOGIKANGIZ JOYLANADI! <<<
@dp.message_handler(content_types=types.ContentType.TEXT)
async def process_link(message: types.Message):
    # Bu funksiya foydalanuvchi havolani yuborganda ishga tushadi.
    # Siz bu yerga yt-dlp yordamida yuklab olish kodini yozishingiz kerak.
    await message.reply(f"Siz havolani yubordingiz: {message.text}. Yuklab olish logikasi shu yerda ishlaydi.")
    
# 3. Serverni Ishga Tushirish uchun Funksiyalar
async def on_startup(dispatcher):
    if not WEBHOOK_URL:
        logging.error("WEBHOOK_URL Railway Variables'da o'rnatilmagan.")
        return
        
    # Telegramga Webhook manzilini o'rnatish
    full_webhook_url = WEBHOOK_URL.rstrip('/') + WEBHOOK_PATH
    await bot.set_webhook(full_webhook_url, drop_pending_updates=True)
    logging.info(f"Webhook o'rnatildi: {full_webhook_url}")

async def on_shutdown(dispatcher):
    logging.warning('Bot o\'chirilmoqda...')
    await bot.delete_webhook()

# 4. FastAPI integratsiyasi
app = FastAPI()

# Telegramdan kelgan so'rovlarni ishlovchi Endpoint
@app.post(WEBHOOK_PATH)
async def telegram_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.process_update(telegram_update)
    return {"message": "ok"}

# 5. Uvicorn Serverini Ishga Tushirish
if __name__ == '__main__':
    uvicorn.run(
        app,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        on_startup=[lambda: on_startup(dp)],
        on_shutdown=[lambda: on_shutdown(dp)]
    )
