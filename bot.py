import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from fastapi import FastAPI
import uvicorn
from yt_dlp import YoutubeDL
from tempfile import TemporaryDirectory

# 1. Konfiguratsiya (Environment Variables Railway)
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN") 
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv("PORT", 8000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL") 
WEBHOOK_PATH = f'/{BOT_TOKEN}'

if not BOT_TOKEN:
    logging.critical("BOT_TOKEN Railway Variables'da o'rnatilmagan!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# 2. Yuklab Olish Funksiyasi (yt-dlp bilan)
async def download_and_send(message: types.Message, url: str):
    await message.reply("⏳ Yuklab olish boshlandi. Iltimos kuting...")
    
    # Yuklab olish uchun vaqtinchalik papka yaratish
    with TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'max_filesize': 500 * 1024 * 1024, # 500 MB limit
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                # Agar video bo'lsa (default format video), yuklab olib yuborish
                ydl.download([url])
                
                # Yuklab olingan faylni topish
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    
                    # Agar audio fayl bo'lsa
                    if filename.endswith(('.mp3', '.m4a')):
                         await bot.send_audio(message.chat.id, audio=open(file_path, 'rb'), caption=info_dict.get('title'))
                    # Agar video fayl bo'lsa
                    elif filename.endswith(('.mp4', '.webm')):
                         await bot.send_video(message.chat.id, video=open(file_path, 'rb'), caption=info_dict.get('title'))
                    
                    os.remove(file_path) # Faylni o'chirish
                    await message.answer("✅ Muvaffaqiyatli yuklandi!")
                    return
                
            await message.reply("Yuklab olish uchun mos format topilmadi.")

        except Exception as e:
            logging.error(f"Yuklab olishda xato: {e}")
            await message.reply(f"❌ Yuklab olishda xato yuz berdi: {e}")


# 3. Telegram Handlerlar
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    await message.reply("Assalomu alaykum! Menga YouTube, Instagram yoki boshqa qo'llab-quvvatlanadigan platforma havolasini yuboring.")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def process_link(message: types.Message):
    url = message.text.strip()
    if url.startswith(('http', 'https')):
        await download_and_send(message, url)
    else:
        await message.reply("Iltimos, to'g'ri havolani yuboring.")

# 4. Serverni Ishga Tushirish uchun Funksiyalar
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

# 5. FastAPI integratsiyasi
app = FastAPI()

# Telegramdan kelgan so'rovlarni ishlovchi Endpoint
@app.post(WEBHOOK_PATH)
async def telegram_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.process_update(telegram_update)
    return {"message": "ok"}

# 6. Uvicorn Serverini Ishga Tushirish
if __name__ == '__main__':
    # Bu blok faqat local (o'zingizda) ishga tushirish uchun, Railway uni e'tiborsiz qoldiradi.
    uvicorn.run(
        app,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        on_startup=[lambda: on_startup(dp)],
        on_shutdown=[lambda: on_shutdown(dp)]
    )
