from odoo import fields, models

class ServiceWorker(models.Model):
    _name = 'service.worker'  
    _description = 'Worker Record'

    name = fields.Char(string='Name', required=True)
    job_title = fields.Char(string='Job Title', required=True)
    age = fields.Integer(string='Age')
    
