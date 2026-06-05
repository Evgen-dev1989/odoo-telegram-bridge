import psycopg2  
from psycopg2.extras import RealDictCursor
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from odoo_client import check_stock_async 

router = Router()



class DBManager:
    def __init__(self, connection_url: str):
        self.url = connection_url

    def _get_connection(self):
        
        return psycopg2.connect(
            host="127.0.0.1",
            database="odoo_test_db",
            user="openpg",
            password="openpg",
            port="5432"
        )
    

class Form(StatesGroup):
    waiting_for_auth = State()
    main_menu = State()
    waiting_for_sku = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: DBManager): 
    is_auth = await db.is_user_authorized(message.from_user.id)
    if is_auth:
        await message.answer("Welcome back! Use /stock to check inventory.")
        await state.set_state(Form.main_menu)
    else:
        phone_button = KeyboardButton(text="📱 Log in via Phone Number", request_contact=True)
        keyboard = ReplyKeyboardMarkup(keyboard=[[phone_button]], resize_keyboard=True, one_time_keyboard=True)
        await message.answer(
            "Welcome! Access is restricted.\n\n"
            "Please share your phone number using the button below, or enter your token:", 
            reply_markup=keyboard
        )
        await state.set_state(Form.waiting_for_auth)


@router.message(Form.waiting_for_auth, F.contact)
async def process_contact_auth(message: Message, state: FSMContext, db: DBManager): 
    phone = message.contact.phone_number
    success = await db.authorize_by_phone(message.from_user.id, phone)
    if success:
        await message.answer("Access granted! Enter /stock.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.main_menu)
    else:
        await message.answer("❌ This phone number is not registered in Odoo. Try entering a token:")


@router.message(Form.waiting_for_auth, F.text)
async def process_token_auth(message: Message, state: FSMContext, db: DBManager):
    token = message.text.strip()
    success = await db.authorize_by_token(message.from_user.id, token)
    if success:
        await message.answer("Token accepted! Enter /stock.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.main_menu)
    else:
        await message.answer("❌ Invalid token. Please try again:")


@router.message(Command("stock"), Form.main_menu)
async def cmd_stock(message: Message, state: FSMContext):
    await message.answer("Please send the product SKU:")
    await state.set_state(Form.waiting_for_sku)


@router.message(Form.waiting_for_sku)
async def process_sku(message: Message, state: FSMContext):
    sku = message.text.strip()
    await message.answer(f"Looking for SKU `{sku}`...")
    result = await check_stock_async(sku)
    
    if result["status"] == "success":
        response = f"📦 *{result['name']}*\n📊 Total available: {result['total']} pcs.\n\n{result['details']}"
    elif result["status"] == "not_found":
        response = f"❌ SKU `{sku}` not found."
    else:
        response = "⚠️ Error connecting to Odoo API."
        
    await message.answer(response, parse_mode="Markdown")
    await state.set_state(Form.main_menu)