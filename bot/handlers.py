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
        if not getattr(self, 'url', None):
            from os import getenv
            raw_url = getenv("DATABASE_URL", "postgresql://openpg:openpg@127.0.0.1:5432/odoo_test_db")
            self.url = str(raw_url).replace('"', '').strip()

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

    def get_product_by_sku(self, sku: str):
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT name, list_price 
                    FROM product_template 
                    WHERE TRIM(default_code) = %s AND active = true 
                    LIMIT 1;""",
                    (str(sku).strip(),) 
                )
                return cur.fetchone()
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
async def process_sku_handler(message: Message):
    sku = message.text.strip()
    
    if not sku:
        await message.answer("Please send a valid SKU.")
        return

    await message.answer(f"Looking for SKU `{sku}` via Odoo API...")
    
    result = await check_stock_async(sku)
    
    if result["status"] == "success":
        name_raw = result["name"]
        
        if isinstance(name_raw, dict):
            product_name = name_raw.get('en_US', 'Unknown Product')
        else:
            product_name = name_raw

        fmt = lambda x: int(x) if x % 1 == 0 else x
        on_hand = fmt(result["on_hand"])
        reserved = fmt(result["reserved"])
        forecasted = fmt(result["forecasted"])
        status_icon = "🟢" if forecasted > 0 else "🔴"

        await message.answer(
            f"📦 **Product Info (Odoo API)**\n\n"
            f"🔹 **Name:** {product_name}\n"
            f"🔹 **SKU:** {sku}\n\n"
            f"📊 **Stock Breakdown:**\n"
            f"📦 **On Hand (physically available):** {on_hand} pcs.\n"
            f"⏳ **Reserved:** {reserved} pcs.\n"
            f"{status_icon} **Available:** {forecasted} pcs."
        )
        
    elif result["status"] == "not_found":
        await message.answer(f"❌ Product with SKU `{sku}` not found in Odoo.")
        
    else:
        await message.answer(f"⚠️ Odoo API Error: {result.get('message', 'Unknown error')}")