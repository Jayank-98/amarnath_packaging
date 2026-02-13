from odoo import models, fields


class DispatchHistory(models.Model):
    """ This model represents dispatch.history."""
    _name = "dispatch.history"
    _description = 'Dispatch History'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner',
        string='Company',
        required=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    dispatch_date = fields.Date(
        string='Dispatch Date'
    )
    quantity = fields.Float(string='Quantity')
    opening_qty = fields.Float(string='Opening Quantity')
    closing_qty = fields.Float(string='Closing Quantity')
