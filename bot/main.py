import asyncio
from os import getenv
from dotenv import load_dotenv

from odoo_client import check_stock_async


load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
ODOO_URL = getenv("ODOO_URL")
ODOO_DB = getenv("ODOO_DB")
ODOO_USER = getenv("ODOO_USER")
ODOO_PASSWORD = getenv("ODOO_PASSWORD")


async def main():
    await check_stock_async()

if __name__ == "__main__":
    asyncio.run(main())