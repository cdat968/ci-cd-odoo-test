from odoo import fields, models


class QaBugTicket(models.Model):
    _inherit = 'qa.bug.ticket'

    helpdesk_ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Helpdesk Ticket',
        copy=False,
        readonly=True,
    )

    def action_open_helpdesk_ticket(self):
        self.ensure_one()
        if not self.helpdesk_ticket_id:
            return False
        action = self.env.ref('helpdesk_mgmt.helpdesk_ticket_action').sudo().read()[0]
        action.update({
            'views': [(self.env.ref('helpdesk_mgmt.ticket_view_form').id, 'form')],
            'res_id': self.helpdesk_ticket_id.id,
            'target': 'current',
        })
        return action
