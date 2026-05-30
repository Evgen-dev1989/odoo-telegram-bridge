import logging
import xmlrpc.client
from os import getenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
from odoo_client import check_stock_async

BOT_TOKEN = getenv("BOT_TOKEN")
ODOO_URL = getenv("ODOO_URL")
ODOO_DB = getenv("ODOO_DB")
ODOO_USER = getenv("ODOO_USER")
ODOO_PASSWORD = getenv("ODOO_PASSWORD")


AUTHORIZED_USERS = {}

SECRET_BOT_TOKEN = "__password"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_token = State()
    main_menu = State()
    waiting_for_sku = State()



@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if message.from_user.id in AUTHORIZED_USERS:
        await message.answer("You have successfully logged in! Enter /stock to check inventory..")
        await state.set_state(Form.main_menu)
    else:
        await message.answer("Welcome. Access is restricted. Please enter your employee authorization token.:")
        await state.set_state(Form.waiting_for_token)

@dp.message(Form.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    if message.text == SECRET_BOT_TOKEN:
        AUTHORIZED_USERS[message.from_user.id] = True
        await message.answer("Authorization successful! You can now check your inventory. Enter /stock.")
        await state.set_state(Form.main_menu)
    else:
        await message.answer("Invalid token. Access denied. Please try again or contact your administrator..")

@dp.message(Command("stock"), Form.main_menu)
async def cmd_stock(message: Message, state: FSMContext):
    await message.answer("Send the product SKU:")
    await state.set_state(Form.waiting_for_sku)

@dp.message(Form.waiting_for_sku)
async def process_sku(message: Message, state: FSMContext):
    sku = message.text.strip()
    await message.answer(f"Looking for item number `{sku}` in Odoo... Please wait.")
    
    # Вызов Odoo без блокировки event loop
    result = await check_stock_async(sku)
    
    if result["status"] == "success":
        response = (
            f"📦 *{result['name']}*\n"
            f"🔢 Article: {sku}\n"
            f"📊 Total available: {result['total']} things.\n\n"
            f"*Details by storage locations:*\n{result['details']}"
        )
    elif result["status"] == "not_found":
        response = f"❌ The product with the article number `{sku}` was not found in the Odoo system.."
    else:
        response = "⚠️ Error connecting to Odoo. Admin notified."
        
    await message.answer(response, parse_mode="Markdown")

    await state.set_state(Form.main_menu)
    await message.answer("You can enter /stock again to check another product.")