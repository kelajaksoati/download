import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from fastapi import FastAPI
import uvicorn # FastAPI bilan ishlatish uchun

# 1. Konfiguratsiyani yuklash
# BOT_TOKEN ni Environment Variables (Railway sozlamalari) orqali olish tavsiya etiladi.
# Agar config.py faylidan o'qimoqchi bo'lsangiz, uni import qiling:
# from config import BOT_TOKEN, CHANNELS 
# Biz hozircha Environment Variable ishlatamiz.
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv("PORT", 8000))

# Loglashni sozlash
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher obyektlari
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# 2. Handler (funksiya) yozish
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    await message.reply("Assalomu alaykum, Instagramax MEGA boti ishlamoqda!")

# 3. Webhook funksiyalarini sozlash
async def on_startup(dispatcher):
    # Bu yerda Webhook manzilini Telegramga o'rnatamiz
    # Sizning xosting manzilingiz bo'lishi kerak. Railway uni avtomatik beradi.
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "SIZNING_RAILWAY_MANZILINGIZ")
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook o'rnatildi: {WEBHOOK_URL}")

async def on_shutdown(dispatcher):
    logging.warning('Bot o\'chmoqda..')
    # Webhookni o'chiramiz
    await bot.delete_webhook()
    logging.warning('Bot o\'chirildi.')

# 4. FastAPI integratsiyasi
app = FastAPI()

# Bu funksiya Telegramdan kelgan har bir yangilanishni (Update) ishlaydi
@app.post("/")
async def telegram_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.process_update(telegram_update)
    return {"message": "ok"}

# 5. Botni ishga tushirish
if __name__ == '__main__':
    # Uvicorn serverini ishga tushirish (FastAPI + Webhook uchun)
    uvicorn.run(
        app,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        on_startup=[lambda: on_startup(dp)],
        on_shutdown=[lambda: on_shutdown(dp)]
    )
