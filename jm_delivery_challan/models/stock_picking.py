# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import re


class StockPicking(models.Model):
    """ This model represents stock.picking."""
    _inherit = 'stock.picking'

    show_price = fields.Boolean(string="Show Price")
    vehicle_number = fields.Char(string='Vehicle No.')
    delivery_person = fields.Char(string='Delivery By')
    # place_of_supply = fields.Char(string='Place of Supply')
    type_code = fields.Selection(
        [('gt', 'GT'),
         ('ap', 'AP')],
        string='Type Code'
    )
    delivery_address = fields.Text(string='Delivery Address')

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if 'type_code' in vals and vals['type_code']:
                name = ''
                if vals['type_code'] == 'gt':
                    name = self.env['ir.sequence'].next_by_code('sale.order.gt')
                elif vals['type_code'] == 'ap':
                    name = self.env['ir.sequence'].next_by_code('sale.order.ap')
                vals['name'] = name
                vals['show_price'] = vals['type_code'] == 'ap'
        return super().create(vals_list)

    def write(self, vals):
        if 'type_code' in vals and vals['type_code']:
            # sequence = self.name.split('-')[-1]  if '-' in self.name else self.name.split('/')[-1]
            name = self.name
            if vals['type_code'] == 'gt':
                name = self.env['ir.sequence'].next_by_code('sale.order.gt')
            elif vals['type_code'] == 'ap':
                name = self.env['ir.sequence'].next_by_code('sale.order.ap')
            vals['name'] = name
            vals['show_price'] = vals['type_code'] == 'ap'
        return super().write(vals)

    @api.onchange('type_code')
    def _onchange_type_code(self):
        if self.type_code:
            self.show_price = self.type_code == 'ap'

    @api.constrains('vehicle_number')
    def _check_vehicle_number_pattern(self):
        """
        Validates vehicle number pattern.
        Must match: 2 letters + 1-2 digits + 1-2 letters + 4 digits
        Example: GJ36AB6908
        """
        pattern = re.compile(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$')
        for record in self:
            if record.vehicle_number and not pattern.match(record.vehicle_number.upper()):
                raise ValidationError(
                    "Invalid Vehicle Number format!\n\n"
                    "Expected format: 2 letters + 1-2 digits + 1-2 letters + 4 digits.\n"
                    "Example: GJ36AB6908"
                )

    def button_validate(self):
        res = super().button_validate()

        for picking in self:
            for move in picking.move_ids:
                process_line = move.process_line_id
                if not process_line:
                    continue

                # This is the incoming delivered qty from stock move
                incoming_qty = move.product_uom_qty
                process_line.delivered_quantity += incoming_qty

                # ----------------------------------------------------
                # 🔥 DISTRIBUTE delivered qty across sale order lines
                # ----------------------------------------------------
                remaining = incoming_qty

                # Sort M2M sale order lines by ID
                solines = process_line.sale_order_line_ids.sorted(key=lambda r: r.id)

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
                    else:
                        # partially fill
                        so_line.qty_delivered += remaining
                        so_line.pending_qty = pending - remaining
                        remaining = 0

                    # Make sure qty_delivered never exceeds ordered qty
                    if so_line.qty_delivered > so_line.product_uom_qty:
                        so_line.qty_delivered = so_line.product_uom_qty
                        so_line.pending_qty = 0
        return res
