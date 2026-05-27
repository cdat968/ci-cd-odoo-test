from odoo import models, fields


class QaFieldOption(models.Model):
    _name = 'qa.field.option'
    _description = 'QA Field Option Tooltip'
    _order = 'field_name, sequence'

    field_name = fields.Char(string='Field Name', required=True, index=True)
    value = fields.Char(string='Option Value', required=True)
    label = fields.Char(string='Display Label', required=True)
    description = fields.Text(string='Tooltip / Explanation')
    sequence = fields.Integer(string='Sequence', default=10)
