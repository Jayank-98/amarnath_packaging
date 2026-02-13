# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProcessOrder(models.Model):
    """ This model represents process.order."""
    _name = 'process.order'
    _description = 'Process Order'
    _order = 'id desc'

    name = fields.Char(string='Process Number', required=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    display_address = fields.Text(string='Address')
    order_line_ids = fields.One2many('process.order.line', 'process_order_id', string='Order Lines')
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('process.order') or '/'
        return super(ProcessOrder, self).create(vals_list)


class ProcessOrderLine(models.Model):
    """ This model represents process.order.line."""
    _name = 'process.order.line'
    _description = 'Process Order Line'
    _rec_name = 'product_id'

    process_order_id = fields.Many2one('process.order', string='Process Order', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='process_order_id.partner_id',
        store=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    sale_order_line_ids = fields.Many2many(
        'sale.order.line',
        string='Sale Order Lines',
        compute='_compute_order_lines')
    order_ids = fields.Many2many(
        'sale.order',
        string='Related Sale Orders',
        compute='_compute_order_lines')
    order_quantity = fields.Float(
        string='Order Quantity',
        required=True,
        compute="_compute_order_quantity",
        digits='Product Unit')
    delivered_quantity = fields.Float(
        string='Delivered Quantity',
        default=0.0, digits='Product Unit')
    pending_quantity = fields.Float(
        string='Pending Quantity',
        compute='_compute_pending_quantity', digits='Product Unit')

    @api.depends('order_quantity', 'delivered_quantity')
    def _compute_pending_quantity(self):
        for line in self:
            line.pending_quantity = line.order_quantity - line.delivered_quantity

    @api.depends('product_id', 'process_order_id.partner_id')
    def _compute_order_lines(self):
        for line in self:
            sale_order_lines = self.env['sale.order.line'].search([
                ('product_id', '=', line.product_id.id),
                ('order_id.partner_id', '=', line.process_order_id.partner_id.id),
                ('state', 'in', ['sale', 'done']),
            ])
            line.sale_order_line_ids = sale_order_lines.ids
            line.order_ids = sale_order_lines.mapped('order_id').ids

    @api.depends('sale_order_line_ids')
    def _compute_order_quantity(self):
        for line in self:
            line.order_quantity = sum(line.sale_order_line_ids.mapped('product_uom_qty'))

    def deliver_quantity_action(self):
        action = {
            'name': f"{self.process_order_id.name} - Dispatch",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'process.order.wizard',
            'target': 'new',
            'context': {
                'default_name': f"{self.process_order_id.partner_id.name} - {self.product_id.name}",
                'default_process_line_id': self.id,
                'default_product_id': self.product_id.id,
                'default_max_quantity': self.pending_quantity
            },
        }
        return action

    def open_dispatch_history(self):
        action = self.env['ir.actions.act_window']._for_xml_id('jm_delivery_challan.action_dispatch_history')
        action['domain'] = [('product_id', '=', self.product_id.id), ('partner_id', '=', self.process_order_id.partner_id.id)]
        action['name'] = f"{self.process_order_id.partner_id.name} - Dispatch History"
        action['target'] = 'new'
        action['context'] = {'search_default_group_partner': 0}
        # action = {
        #     'name': f"{self.process_order_id.name} - Dispatch History",
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'list',
        #     'res_model': 'process.order.wizard',
        #     'target': 'new',
        #     'domain': [('process_line_id', '=', self.id)],
        # }
        return action
