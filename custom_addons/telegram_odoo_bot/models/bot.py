import asyncio
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

BOT_TOKEN = getenv("BOT_TOKEN")
ODOO_URL = getenv("ODOO_URL")
ODOO_DB = getenv("ODOO_DB")
ODOO_USER = getenv("ODOO_USER")
ODOO_PASSWORD = getenv("ODOO_PASSWORD")