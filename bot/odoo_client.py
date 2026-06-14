import asyncio
import logging
import xmlrpc.client
from os import getenv


ODOO_URL = str(getenv("ODOO_URL", "http://127.0.0.1:8069")).replace('"', '').replace("'", "").strip()
ODOO_DB = str(getenv("ODOO_DB", "odoo_test_db")).replace('"', '').replace("'", "").strip()
ODOO_USER = str(getenv("ODOO_USER", "admin")).replace('"', '').replace("'", "").strip()
ODOO_PASSWORD = str(getenv("ODOO_PASSWORD", "admin")).replace('"', '').replace("'", "").strip()


if not ODOO_URL.startswith('http://') and not ODOO_URL.startswith('https://'):
    ODOO_URL = f"http://{ODOO_URL}"


def _get_odoo_uid():
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    
    if not uid:
        raise ValueError("Incorrect Odoo credentials (DB name, User or Password)")
    return uid


def _check_stock_in_odoo(sku: str) -> dict:
    try:
        uid = _get_odoo_uid()
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', allow_none=True)
        
        products = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.product', 'search_read',
            [[['default_code', '=', sku]]],
            {
                'fields': [
                    'display_name', 
                    'qty_available',      
                    'outgoing_qty',       
                    'virtual_available'  
                ], 
                'limit': 1
            }
        )
        
        if not products:
            return {"status": "not_found"}
        
        product = products[0]
        
        return {
            "status": "success",
            "name": product['display_name'],
            "on_hand": product['qty_available'],
            "reserved": product['outgoing_qty'],
            "forecasted": product['virtual_available']
        }
    except Exception as e:
        logging.error(f"Odoo Error: {e}")
        return {"status": "error", "message": str(e)}


async def check_stock_async(sku: str) -> dict:
    return await asyncio.to_thread(_check_stock_in_odoo, sku)