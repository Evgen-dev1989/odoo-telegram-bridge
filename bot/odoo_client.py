import asyncio
import logging
import xmlrpc.client
from os import getenv
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
ODOO_URL = getenv("ODOO_URL")
ODOO_DB = getenv("ODOO_DB")
ODOO_USER = getenv("ODOO_USER")
ODOO_PASSWORD = getenv("ODOO_PASSWORD")

def _get_odoo_uid():
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    return common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

def _check_stock_in_odoo(sku: str) -> dict:
    try:
        uid = _get_odoo_uid()
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        product_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'search',
            [[['default_code', '=', sku]]]
        )
        
        if not product_ids:
            return {"status": "not_found"}
        
        product_id = product_ids[0]
        
        quants = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.quant', 'search_read',
            [[['product_id', '=', product_id], ['location_id.usage', '=', 'internal']]],
            {'fields': ['location_id', 'quantity']}
        )
        
  
        stock_details = []
        total_qty = 0
        for q in quants:
            qty = q['quantity']
            if qty > 0:
                stock_details.append(f"📍 {q['location_id'][1]}: {qty} шт.")
                total_qty += qty
                
        return {
            "status": "success",
            "name": quants[0]['product_id'][1] if quants else "Товар найден",
            "total": total_qty,
            "details": "\n".join(stock_details) if stock_details else "На складах пусто"
        }
    except Exception as e:
        logging.error(f"Odoo Error: {e}")
        return {"status": "error", "message": str(e)}


async def check_stock_async(sku: str) -> dict:

    return await asyncio.to_thread(_check_stock_in_odoo, sku)