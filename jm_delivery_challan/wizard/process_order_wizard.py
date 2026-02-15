# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProcessOrderWizard(models.TransientModel):
    """ This model represents process.order.wizard."""
    _name = 'process.order.wizard'
    _description = 'Process Order Wizard'

    name = fields.Char(string='Name')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product'
    )
    process_line_id = fields.Many2one("process.order.line", string="Process Line")
    quantity = fields.Float(string="Quantity")
    max_quantity = fields.Float(string="Max. Quantity")
    pending_qty = fields.Float(string="Pending Quantity", compute="_compute_pending_quantity")

    @api.depends("quantity")
    def _compute_pending_quantity(self):
        for rec in self:
            rec.pending_qty = rec.max_quantity - rec.quantity

    def action_confirm(self):
        """ Update the quantity of the selected product."""
        for record in self:
            if record.quantity > record.max_quantity:
                raise UserError("Quantity Can't be more than Maximum Quantity.!")
            order_ids = []
            if record.process_line_id:
                record.process_line_id.write({
                    'delivered_quantity':
                        record.process_line_id.delivered_quantity + record.quantity
                })
                solines = record.process_line_id.sale_order_line_ids.sorted(key=lambda r: r.id)
                remaining = record.quantity

                for so_line in solines:
                    if remaining <= 0:
                        break

                    pending = so_line.product_uom_qty - so_line.qty_delivered

                    if pending <= 0:
                        continue

                    if remaining >= pending:
                        # fill completely
                        so_line.qty_delivered += pending
                        remaining -= pending
                        so_line.pending_qty = 0
                        if so_line.order_id.id not in order_ids:
                            order_ids.append(so_line.order_id.id)
                    else:
                        # partially fill
                        so_line.qty_delivered += remaining
                        so_line.pending_qty = pending - remaining
                        remaining = 0
                        if so_line.order_id.id not in order_ids:
                            order_ids.append(so_line.order_id.id)

                    # Make sure qty_delivered never exceeds ordered qty
                    if so_line.qty_delivered > so_line.product_uom_qty:
                        so_line.qty_delivered = so_line.product_uom_qty
                        so_line.pending_qty = 0
                        if so_line.order_id.id not in order_ids:
                            order_ids.append(so_line.order_id.id)
            # ============================
            # CREATE DISPATCH HISTORY HERE
            # ============================
            self.env["dispatch.history"].create({
                "partner_id": record.process_line_id.process_order_id.partner_id.id,
                "product_id": record.product_id.id,
                "dispatch_date": fields.Date.today(),
                "quantity": record.quantity,
                "opening_qty": record.max_quantity,
                "closing_qty": record.max_quantity - record.quantity,
                "order_ids": order_ids
            })
        return True
