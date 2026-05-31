import asyncio
import logging
from os import getenv
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import selectors

from handlers import router, DBManager 

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
PG_URL = getenv("PG_URL")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    db = DBManager(PG_URL)
    
    dp["db"] = db
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    

    try:
        await dp.start_polling(bot)
    finally:

        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(
            main(), 
            loop_factory=asyncio.SelectorEventLoop
        )
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user")