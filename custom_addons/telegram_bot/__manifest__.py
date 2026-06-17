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

#celery -A bot.celery_app worker --loglevel=info -P solo
#celery -A bot.celery_app beat --loglevel=info

