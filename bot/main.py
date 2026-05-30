import asyncio
import logging
from os import getenv
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

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
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())