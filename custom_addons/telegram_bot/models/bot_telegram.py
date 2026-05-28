import secrets
import re
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ServiceWorker(models.Model):
    _name = 'servise.worker' 
    _description = 'Worker Record'

    name = fields.Char(string='Name', required=True)
    job_title = fields.Char(string='Job Title', required=True)
    age = fields.Integer(string='Age')
    
    user_id = fields.Many2one(
        'res.users', 
        string='Odoo User', 
        help="Associated Odoo user (if you have a paid license)"
    )
    

    phone = fields.Char(
        string='Phone Number', 
        index=True,
        help="Format: +38(097)0290351. Used for authorization in the bot."
    )

    telegram_chat_id = fields.Char(string='Telegram Chat ID', copy=False, index=True)

    telegram_auth_token = fields.Char(
        string='Telegram Auth Token', 
        copy=False, 
        readonly=True, 
        index=True
    )
    
    tg_connected = fields.Boolean(
        string='Telegram Connected', 
        compute='_tg_connected', 
        store=True
    )

    @api.depends('telegram_chat_id')
    def _tg_connected(self):
        for record in self:
            record.tg_connected = bool(record.telegram_chat_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('telegram_auth_token') and not vals.get('telegram_chat_id'):
                vals['telegram_auth_token'] = f"tg_{secrets.token_hex(8)}"
        return super(ServiceWorker, self).create(vals_list)

    def action_regenerate_tg_token(self):
        for record in self:
            record.write({
                'telegram_auth_token': f"tg_{secrets.token_hex(8)}",
                'telegram_chat_id': False
            })


    @api.constrains('phone')
    def _check_phone_format(self):
        for record in self:
            if record.phone:
                clean_phone = re.sub(r'\D', '', record.phone)
                if len(clean_phone) < 10 or len(clean_phone) > 15:
                    raise ValidationError("The phone number must contain between 10 and 15 digits.")