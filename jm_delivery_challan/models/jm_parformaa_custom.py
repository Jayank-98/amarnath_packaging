# -*- coding: utf-8 -*-
from odoo import api, fields, models


class JmParformaaCustom(models.Model):
    """ This model represents jm.parformaa.custom."""
    _inherit = 'parffoma.order'

    sale_order_line_id = fields.Many2one(
        'sale.order.line', string='Sale Order Line', tracking=True)
    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order',
        tracking=True,
        related='sale_order_line_id.order_id')
    parformma_status = fields.Selection([
        ('not_created', 'Not Created'),
        ('created', 'Created'),
        ('processed', 'Processed'),
        ('done', 'Done'),
    ], string='Parformma Status', default='created', tracking=True)

    @api.onchange(
        'order_no', 'date', 'company_id',
        'company_name', 'product_id', 'printing',
        'box_qty', 'b_value', 'h_value',
        'l_value', 'f_value', 'paper_decal',
        'paper_cutting', 'top_paper_qty', 'top_paper_gsm',
        'bottom_liner_qty', 'bottom_liner_gsm', 'note', 'ply_type')
    def _onchange_parformma_status(self):
        BASIC_FIELDS = {
            'order_no', 'date', 'company_id', 'company_name',
            'product_id', 'box_qty'
        }

        ALL_FIELDS = {
            'order_no', 'date', 'company_id', 'company_name', 'product_id',
            'printing', 'box_qty', 'b_value', 'h_value', 'l_value', 'f_value',
            'paper_decal', 'paper_cutting',
            'top_paper_qty', 'top_paper_gsm',
            'bottom_liner_qty', 'bottom_liner_gsm',
            'note', 'ply_type'
        }

        for order in self:
            if not order:
                order.parformma_status = 'not_created'
                continue

            # Check if ALL fields are filled → DONE
            all_filled = all(order[field] not in (False, None, '') for field in ALL_FIELDS)

            if all_filled:
                order.parformma_status = 'done'
                continue

            # Check if ONLY basic fields are filled → CREATED
            other_fields_filled = False

            for field in ALL_FIELDS:
                if field not in BASIC_FIELDS:
                    value = order[field]
                    if value not in (False, None, ''):
                        other_fields_filled = True
                        break

            if not other_fields_filled:
                order.parformma_status = 'created'
            else:
                order.parformma_status = 'processed'
