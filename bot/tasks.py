import logging
import xmlrpc.client
from aiogram import Bot
import asyncio
from os import getenv
from celery_app import app

ODOO_URL = str(getenv("ODOO_URL", "http://127.0.0.1:8069")).replace('"', '').strip()
ODOO_DB = str(getenv("ODOO_DB", "odoo_test_db")).replace('"', '').strip()
ODOO_USER = str(getenv("ODOO_USER", "admin")).replace('"', '').strip()
ODOO_PASSWORD = str(getenv("ODOO_PASSWORD", "admin")).replace('"', '').strip()

TELEGRAM_TOKEN = getenv("BOT_TOKEN")
ADMIN_CHAT_ID = getenv("admin_id")

STOCK_LIMITS = {
    "FURN_7777": 300,  
    "FURN_8888": 10,  
}

@app.task(name="bot.celery_app.check_stock_limits_task")
def check_stock_limits_task():
    logging.info("Celery task: Starting stock limits check...")
    
    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID:
        logging.error("Celery Task Error: TELEGRAM_TOKEN or ADMIN_CHAT_ID missing in .env")
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