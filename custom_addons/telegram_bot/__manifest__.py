{
    'name': 'Telegram Bot Bridge for Warehouse',
    'version': '1.0',
    'category': 'Inventory/Warehouse',
    'summary': 'API endpoints and access rights for Telegram Bot integration',
    'author': 'Evgeny',
    'depends': ['stock'],  
    'data': [
  
    ],  
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

#python odoo/odoo-bin -c odoo.conf -d odoo_test_db -i telegram_bot

#python odoo/odoo-bin -c odoo.conf --db_host=localhost --db_port=5432 --db_user=openpg --db_password=openpg -d odoo_test_db