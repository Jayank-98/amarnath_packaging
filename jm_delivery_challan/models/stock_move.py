# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import re
from odoo.exceptions import UserError


class StockMove(models.Model):
    """ This model represents stock.move."""
    _inherit = 'stock.move'

    bundle = fields.Integer(string='Bundle')
    packing = fields.Integer(string='Packing')
    loose_qty = fields.Float(string='Loose Qty')
    price_unit = fields.Float(string='Price Unit')
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_price_subtotal')
    process_line_id = fields.Many2one(
        "process.order.line",
        string="Process Order Line")
    process_order_id = fields.Many2one(
        "process.order",
        string="Process Order",
        compute="_compute_process_order_id")
    allow_product_ids = fields.Many2many(
        "product.product",
        string="Allowed Products")
    product_id = fields.Many2one(
        'product.product', 'Product',
        check_company=True,
        domain="[('type', '=', 'consu'), ('id', 'in', allow_product_ids)]",
        index=True, required=True)

    @api.depends('picking_id.partner_id')
    def _compute_process_order_id(self):
        for rec in self:
            process_order = self.env['process.order'].search([
                ('partner_id', '=', rec.partner_id.id)
            ], limit=1)
            rec.process_order_id = process_order.id if process_order else False
            rec.allow_product_ids =\
                process_order.order_line_ids.filtered(
                    lambda l: l.pending_quantity > 0).mapped('product_id').ids\
                    if process_order and process_order.order_line_ids else False

    @api.onchange('product_id')
    def _onchange_product_id_set_process_line_id(self):
        for rec in self:
            if rec.process_order_id and rec.product_id:
                process_line = self.env['process.order.line'].search([
                    ('process_order_id', '=', rec.process_order_id.id),
                    ('product_id', '=', rec.product_id.id)
                ], limit=1)
                rec.process_line_id = process_line.id if process_line else False
                rec.product_uom_qty = process_line.pending_quantity if process_line else 0.0

    @api.depends('price_unit', 'quantity', 'product_uom_qty')
    def _compute_price_subtotal(self):
        for move in self:
            quantity = move.quantity or move.product_uom_qty
            move.price_subtotal = move.price_unit * quantity

    @api.onchange('bundle', 'packing', 'loose_qty')
    def _compute_packing(self):
        for move in self:
            if move.bundle < 0 or move.packing < 0 or move.loose_qty < 0:
                raise UserError("Bundle, Packing and Loose Qty must be non-negative.")
            total_qty = move.bundle * move.packing + move.loose_qty
            move.product_uom_qty = total_qty
