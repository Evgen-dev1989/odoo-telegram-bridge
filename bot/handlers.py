import psycopg2  
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from os import getenv
from odoo_client import check_stock_async 

router = Router()

BOT_TOKEN = getenv("BOT_TOKEN")
PG_URL = getenv("PG_URL")


host = getenv("host")
database = getenv("database")
user=getenv("user")
password = getenv("password")
port = getenv("port")


class DBManager:
    def __init__(self, connection_url: str):
        self.url = connection_url

    def _get_connection(self):

        clean_url = self.url.replace("localhost", "127.0.0.1")
        return psycopg2.connect(clean_url)
    
    async def is_user_authorized(self, tg_id: int) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM servise_worker WHERE telegram_chat_id = %s LIMIT 1;",
                    (str(tg_id),)
                )
                result = cur.fetchone()
                return result is not None
        finally:
            conn.close()
    

    async def authorize_by_token(self, tg_id: int, token: str) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM servise_worker WHERE telegram_auth_token = %s LIMIT 1;",
                    (token,)
                )
                worker = cur.fetchone()
                
                if worker:
                    worker_id = worker[0]
                    cur.execute(
                        """UPDATE servise_worker 
                           SET telegram_chat_id = %s, telegram_auth_token = NULL 
                           WHERE id = %s;""",
                        (str(tg_id), worker_id)
                    )
                    conn.commit() 
                    return True
                return False
        finally:
            conn.close()


    async def authorize_by_phone(self, tg_id: int, phone: str) -> bool:

        clean_phone = phone.replace("+", "").strip()
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id FROM servise_worker 
                       WHERE phone = %s OR phone = %s LIMIT 1;""",
                    (clean_phone, f"+{clean_phone}")
                )
                worker = cur.fetchone()
                
                if worker:
                    worker_id = worker[0]
                    cur.execute(
                        "UPDATE servise_worker SET telegram_chat_id = %s WHERE id = %s;",
                        (str(tg_id), worker_id)
                    )
                    conn.commit()
                    return True
                return False
        finally:
            conn.close()



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