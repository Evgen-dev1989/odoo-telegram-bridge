import os
import sys
import logging
import xmlrpc.client
import asyncio
from celery import Celery
from celery.schedules import crontab
from aiogram import Bot

ODOO_URL = str(os.getenv("ODOO_URL", "http://127.0.0.1:8069")).replace('"', '').strip()
ODOO_DB = str(os.getenv("ODOO_DB", "odoo_test_db")).replace('"', '').strip()
ODOO_USER = str(os.getenv("ODOO_USER", "admin")).replace('"', '').strip()
ODOO_PASSWORD = str(os.getenv("ODOO_PASSWORD", "admin")).replace('"', '').strip()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

REDIS_URL = "redis://127.0.0.1:6379/0" 

app = Celery(
    "stock_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

app.conf.update(
    timezone="Europe/Kyiv",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)


STOCK_LIMITS = {
    "FURN_7777": 300,
}

@app.task(name="check_stock_limits_task")
def check_stock_limits_task():
    logging.info("Celery task: Starting stock limits check...")

    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID:
        logging.error("Celery Task Error: Config missing in .env")
        return "Missing TG Config"

    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common', allow_none=True)
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        if not uid:
            return "Odoo Auth Failed"
            
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', allow_none=True)
        alerts = []
        
        for sku, min_limit in STOCK_LIMITS.items():
            products = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.product', 'search_read',
                [[['default_code', '=', sku]]],
                {'fields': ['display_name', 'virtual_available'], 'limit': 1}
            )
            
            if products:
                product = products[0]
                current_forecast = product['virtual_available']
                product_name = product['display_name']
                
                if current_forecast < min_limit:
                    alerts.append(
                        f"⚠️ **{product_name}** (SKU: `{sku}`)\n"
                        f"❌ Stock dropped to: **{int(current_forecast)}** pcs.\n"
                        f"🛑 Minimum limit: **{min_limit}** pcs.\n"
                        f"📦 Reorder required: 🛒 **{int(min_limit - current_forecast)}** pcs.\n"
                    )
        
        if alerts:
            bot = Bot(token=TELEGRAM_TOKEN)
            message_text = "🚨 **LOW STOCK REPORT** 🚨\n\n" + "\n".join(alerts)
            asyncio.run(bot.send_message(chat_id=ADMIN_CHAT_ID, text=message_text, parse_mode="Markdown"))
            return f"Sent {len(alerts)} alerts."
            
        return "All stocks are OK"

    except Exception as e:
        logging.error(f"Celery Stock Task Error: {e}")
        return f"Error: {e}"


app.conf.beat_schedule = {
    "check-stock-every-minute": {
        "task": "check_stock_limits_task", 
        "schedule": 60.0,  
    },
}