from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

#_logger.info(" ТЕКСТ : %s ", self.custom_requirements)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    custom_requirements = fields.Text(string='Особые требования')


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def _register_hook(self):
        """Этот метод вызывается автоматически при старте Odoo"""
        super(IrUiView, self)._register_hook()
        
        xml_id = 'my_crm_extension.view_crm_lead_form_inherit'
        
        self.env.cr.execute("DELETE FROM ir_ui_view WHERE key = %s", (xml_id,))
        
        # 2. Создаем ОДНУ чистую, свежую запись интерфейса
        base_view = self.env.ref('crm.crm_lead_view_form', raise_if_not_found=False)
        
        if base_view:
            arch_content = """
                <xpath expr="//field[@name='tag_ids']" position="after">
                    <field name="custom_requirements" placeholder="Например: Доставка только в выходные..."/>
                </xpath>
            """
            
            self.create({
                'name': 'crm.lead.form.inherit.my.extension',
                'model': 'crm.lead',
                'mode': 'extension',
                'inherit_id': base_view.id,
                'arch': arch_content,
                'key': xml_id,
            })