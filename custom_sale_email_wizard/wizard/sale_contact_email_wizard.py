from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleContactEmailWizard(models.TransientModel):
    _name = 'sale.contact.email.wizard'
    _description = 'Sale Contact Email Wizard'

    order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='order_id.partner_id')
    contact_line_ids = fields.One2many('sale.contact.email.line', 'wizard_id', string='Contacts')
    subject = fields.Char(string='Subject', required=True)
    body = fields.Html(string='Message Body')
    template_id = fields.Many2one('mail.template', string='Email Template',
                                  domain="[('model', '=', 'sale.order')]")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            order = self.env['sale.order'].browse(self.env.context['active_id'])
            res['order_id'] = order.id

            # Get default template
            template = self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
            if template:
                res['template_id'] = template.id
                res['subject'] = template.subject
                res['body'] = template.body_html
            else:
                res['subject'] = f'Quotation - {order.name}'

            # Load contacts
            contacts = []
            if order.partner_id:
                # Add main contact
                if order.partner_id.email:
                    contacts.append({
                        'contact_id': order.partner_id.id,
                        'email': order.partner_id.email,
                        'selected': True,
                    })

                # Add child contacts
                child_partners = order.partner_id.child_ids.filtered(lambda p: p.email and not p.is_company)
                for partner in child_partners:
                    contacts.append({
                        'contact_id': partner.id,
                        'email': partner.email,
                        'selected': False,
                    })

            res['contact_line_ids'] = [(0, 0, contact) for contact in contacts]

        return res

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id and self.order_id:
            template = self.template_id.with_context(lang=self.partner_id.lang)
            self.subject = template.subject
            self.body = template.body_html

    def action_send_email(self):
        """Send email to selected contacts"""
        if not self.contact_line_ids.filtered('selected'):
            raise UserError("Please select at least one contact to send the email.")

        selected_contacts = self.contact_line_ids.filtered('selected')
        recipients = [contact.email for contact in selected_contacts]

        # Prepare email values
        email_values = {
            'subject': self.subject,
            'body_html': self.body,
            'email_to': ','.join(recipients),
            'email_from': self.env.user.email_formatted,
            'reply_to': self.env.user.email_formatted,
            'model': 'sale.order',
            'res_id': self.order_id.id,
        }

        # Send email
        mail = self.env['mail.mail'].create(email_values)
        mail.send()

        # Mark quotation as sent
        if self.order_id.state == 'draft':
            self.order_id.state = 'sent'

        # Log activity
        self.order_id.message_post(
            body=f"Quotation sent to: {', '.join(recipients)}",
            subject=self.subject,
        )

        return {'type': 'ir.actions.act_window_close'}

    def action_preview(self):
        """Preview the email before sending"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Email Preview',
            'res_model': 'sale.contact.email.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'preview_mode': True}
        }

    def action_add_contact(self):
        """Open form to add new contact"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Contact',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parent_id': self.partner_id.id,
                'default_is_company': False,
            }
        }


class SaleContactEmailLine(models.TransientModel):
    _name = 'sale.contact.email.line'
    _description = 'Sale Contact Email Line'

    wizard_id = fields.Many2one('sale.contact.email.wizard', string='Wizard', ondelete='cascade')
    contact_id = fields.Many2one('res.partner', string='Contact', required=True)
    email = fields.Char(string='Email', required=True)
    selected = fields.Boolean(string='Send Email', default=False)

    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        if self.contact_id:
            self.email = self.contact_id.email