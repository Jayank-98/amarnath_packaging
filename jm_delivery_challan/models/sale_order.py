# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    """ This model represents sale.order."""
    _inherit = 'sale.order'

    delivery_address = fields.Text(string='Delivery Address')
    total_order = fields.Float(string='Total Order', compute='_compute_total_quantity')
    total_delivered = fields.Float(string='Total Delivered', compute='_compute_total_quantity')
    total_pending = fields.Float(string='Total Pending', compute='_compute_total_quantity')
    delivery_status_cust = fields.Selection([
        ('pending', 'Not Delivered'),
        ('started', 'Started'),
        ('partial', 'Partially Delivered'),
        ('full', 'Fully Delivered'),
    ], string='Delivery Status', compute='_compute_delivery_status_cust')
    parfomma_orders_count = fields.Integer(
        string='Parforma Orders Count',
        compute='_compute_parforma_orders_count'
    )
    parformma_status = fields.Selection([
        ('not_created', 'Not Created'),
        ('created', 'Created'),
        ('partially_created', 'Partially Created'),
        ('processed', 'Processed'),
        ('done', 'Done'),
    ], string='Parformma Status', compute='_compute_parformma_status', store=True)
    manufacturing_type = fields.Selection([
        ('single_liner', 'Single Liner'),
        ('double_liner', 'Double Liner'),
        ('both', 'Both')], string='Manufacturing Type')

    @api.model
    def default_get(self, fields):
        """If we're creating a new account through a many2one, there are chances that we typed the account code
        instead of its name. In that case, switch both fields values.
        """
        defaults = super(SaleOrder, self).default_get(fields)
        if 'manufacturing_type' in fields:
            default_manufacturing_type = self.env['ir.config_parameter'].sudo().get_param(
                'jm_parformma_custom.manufacturing_type')
            defaults['manufacturing_type'] = default_manufacturing_type
        return defaults

    @api.depends('order_line.parformma_status')
    def _compute_parformma_status(self):
        for order in self:
            statuses = order.mapped('order_line.parformma_status')

            if not statuses:
                order.parformma_status = 'not_created'
                continue

            # Priority: done → processed → created/partial → not_created
            if all(s == 'done' for s in statuses):
                order.parformma_status = 'done'

            elif any(s == 'processed' for s in statuses):
                order.parformma_status = 'processed'

            elif all(s == 'created' for s in statuses):
                order.parformma_status = 'created'

            elif 'created' in statuses and False in statuses:
                order.parformma_status = 'partially_created'

            elif all(s == 'not_created' for s in statuses):
                order.parformma_status = 'not_created'

            else:
                # fallback safety
                order.parformma_status = 'not_created'

    def _compute_parforma_orders_count(self):
        for order in self:
            order.parfomma_orders_count = self.env['parffoma.order'].search_count([
                ('sale_order_id', '=', order.id)
            ])

    def action_open_parformma_orders(self):
        """ Open Parffoma Orders related to this Sale Order """
        self.ensure_one()
        return {
            'name': 'Parffoma Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'parffoma.order',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }

    def create_parforma_orders(self):
        """ Create Parffoma Orders from Sale Order Lines """
        for order in self:
            for line in order.order_line:
                parformma_order_id = self.env['parffoma.order'].create({
                    'company_name': order.partner_id.id,
                    'product_id': line.product_id.id if line.product_id else False,
                    'printing': line.printing_note_id.name if line.printing_note_id else '',
                    'date': order.date_order,
                    'box_qty': line.product_uom_qty,
                    'ply_type': line.ply_option_id.name,
                    'sale_order_line_id': line.id,
                    'sale_order_id': order.id,
                    'company_id': order.company_id.id,
                    # Add other necessary fields as required
                })
                line.parformma_order_id = parformma_order_id.id

    @api.depends('total_order', 'total_delivered', 'total_pending')
    def _compute_delivery_status_cust(self):
        for order in self:
            if order.total_pending == order.total_order:
                order.delivery_status_cust = 'pending'
            elif order.total_pending <= 0:
                order.delivery_status_cust = 'full'
            elif 0 < order.total_pending < order.total_order:
                order.delivery_status_cust = 'partial'
            else:
                order.delivery_status_cust = 'started'

    def _compute_total_quantity(self):
        for order in self:
            total_order = sum(line.product_uom_qty for line in order.order_line)
            total_delivered = sum(line.qty_delivered for line in order.order_line)
            total_pending = total_order - total_delivered
            order.total_order = total_order
            order.total_delivered = total_delivered
            order.total_pending = total_pending

    @api.model
    def create(self, vals_list):
        records = super(SaleOrder, self).create(vals_list)
        records.with_context(skip_procurement=True).action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            for record in records:
                record.action_lock()
        return records

    def action_confirm(self):
        """Override confirm to update/create Process Order"""
        res = super(SaleOrder, self).action_confirm()
        self.create_edit_process_order()
        # self.create_parforma_orders()
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'order_line' in vals:
            self.create_edit_process_order()
        return res

    def create_edit_process_order(self):
        """ Create or Edit Process Order based on Sale Order Lines """
        for order in self:
            customer = order.partner_id

            # ---------------------------------------------
            # 1. Find existing Process Order for customer
            # ---------------------------------------------
            process_order = self.env['process.order'].search([
                ('partner_id', '=', customer.id),
                ('active', '=', True)
            ], limit=1)

            # ---------------------------------------------
            # 2. If not found → create new Process Order
            # ---------------------------------------------
            if not process_order:
                process_order = self.env['process.order'].create({
                    'partner_id': customer.id,
                })

            # ---------------------------------------------
            # 3. Process each sale order line
            # ---------------------------------------------
            for sol in order.order_line:
                product = sol.product_id

                # find existing process order line for same product
                existing_line = process_order.order_line_ids.filtered(
                    lambda l: l.product_id.id == product.id
                )

                if existing_line:
                    # Update existing line quantity
                    existing_line.order_quantity += sol.product_uom_qty
                else:
                    # Create new process order line
                    self.env['process.order.line'].create({
                        'process_order_id': process_order.id,
                        'product_id': product.id,
                        'order_quantity': sol.product_uom_qty,
                    })

class SaleOrderLine(models.Model):
    """ This model represents sale.order.line."""
    _inherit = 'sale.order.line'

    ply_option_id = fields.Many2one("ply.options", string='Ply Options')
    pending_qty = fields.Float(string='Pending Qty', compute='_compute_pending_qty')
    parformma_order_id = fields.Many2one(
        'parffoma.order', string='Parffoma Order', tracking=True, copy=False)
    parformma_status = fields.Selection([
        ('not_created', 'Not Created'),
        ('created', 'Created'),
        ('processed', 'Processed'),
        ('done', 'Done'),
    ], string='Parformma Status',
        related='parformma_order_id.parformma_status',
        default='not_created',store=True, copy=False)
    printing = fields.Char(string='Printing', tracking=True)
    printing_note_id = fields.Many2one('printing.note', string='Printing Note', tracking=True)
    manufacturing_type = fields.Selection([
        ('single_liner', 'Single Liner'),
        ('double_liner', 'Double Liner')], string='Manufacturing Type')

    @api.model
    def default_get(self, fields):
        """If we're creating a new account through a many2one, there are chances that we typed the account code
        instead of its name. In that case, switch both fields values.
        """
        defaults = super(SaleOrderLine, self).default_get(fields)
        if 'manufacturing_type' in fields:
            default_manufacturing_type = self.env['ir.config_parameter'].sudo().get_param(
                'jm_parformma_custom.manufacturing_type')
            defaults['manufacturing_type'] = default_manufacturing_type if default_manufacturing_type != 'both' else ''
        return defaults

    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_pending_qty(self):
        for line in self:
            line.pending_qty = line.product_uom_qty - line.qty_delivered

    def action_open_parformma_orders(self):
        """ Open Parffoma Orders related to this Sale Order Line """
        self.ensure_one()
        return {
            'name': 'Parffoma Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'parffoma.order',
            'view_mode': 'form',
            'res_id': self.parformma_order_id.id or False,
            'target': 'new',
            'context': {
                'default_sale_order_id': self.order_id.id,
                'default_sale_order_line_id': self.id
            },
        }

    def create_parforma_orders(self):
        """ Create Parffoma Orders from Sale Order Lines """
        for line in self:
            order = line.order_id
            parformma_order_id = self.env['parffoma.order'].create({
                'company_name': order.partner_id.id,
                'product_id': line.product_id.id if line.product_id else False,
                'printing_note_id': line.printing_note_id.id if line.printing_note_id else '',
                'date': order.date_order,
                'box_qty': line.product_uom_qty,
                'top_paper_qty': line.product_uom_qty,
                'top_liner_qty': line.product_uom_qty,
                'manufacturing_type': line.manufacturing_type,
                'bottom_liner_qty': line.product_uom_qty,
                'ply_option_id': line.ply_option_id.id if line.ply_option_id else False,
                'sale_order_line_id': line.id,
                'sale_order_id': order.id,
                'company_id': order.company_id.id,
                # Add other necessary fields as required
            })
            line.parformma_order_id = parformma_order_id.id
