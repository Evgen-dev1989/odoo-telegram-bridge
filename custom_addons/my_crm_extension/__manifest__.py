{
    'name': 'My CRM Extension',
    'version': '1.0',
    'category': 'Sales/CRM',
    'depends': ['crm'],
    'data': [],  # ТУТ СТРОГО ПУСТО
    'installable': True,
    'license': 'LGPL-3',
}

#python odoo/odoo-bin -c odoo.conf -d odoo_test_db -i my_crm_extension