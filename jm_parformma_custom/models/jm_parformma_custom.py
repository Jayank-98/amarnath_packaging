# jm_custom_parffoma/models/parffoma_order.py
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re


class ParffomaOrder(models.Model):
    _name = 'parffoma.order'
    _description = 'Parffoma Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'order_no desc'

    order_no = fields.Char(string='Order No', default="New", required=True, copy=False)
    date = fields.Date(string='Date', default=fields.Date.today, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', tracking=True,
        default=lambda self: self.env.company)
    company_name = fields.Many2one(
        "res.partner",
        string='Company Name',
        tracking=True,
        required=True
    )
    product_name = fields.Char(string='Product Name', tracking=True, required=True)
    printing = fields.Char(string='Printing', tracking=True)
    box_qty = fields.Integer(string='Box Quantity', tracking=True)

    # Dimensions
    b_value = fields.Char(string='B', tracking=True)
    h_value = fields.Char(string='H', tracking=True)
    l_value = fields.Char(string='L', tracking=True)
    f_value = fields.Char(string='F', tracking=True)

    # Paper details
    paper_decal = fields.Float(string='Paper Decal', tracking=True)
    paper_cutting = fields.Float(string='Paper Cutting', tracking=True)

    top_paper_qty = fields.Integer(string='Top Paper Qty', tracking=True)
    top_paper_gsm = fields.Char(string='Top Paper GSM/BF', tracking=True)

    top_liner_qty = fields.Integer(string='Top Liner Qty', tracking=True)
    bottom_liner_qty = fields.Integer(string='Bottom Liner Qty', tracking=True)
    bottom_liner_gsm = fields.Char(string='Bottom Liner GSM/BF', tracking=True)
    top_liner_gsm = fields.Char(string='Top Liner GSM/BF', tracking=True)

    note = fields.Text(string='Note', tracking=True)
    ply_type = fields.Char(string='Ply Type', tracking=True)

    # Example computed field: full description
    full_description = fields.Text(
        string='Full Description',
        compute='_compute_full_description'
    )

    paper_id = fields.Many2one("paper.type", string="Paper", tracking=True)
    top_paper_color = fields.Selection([('golden', 'Golden'), ('lwc', 'LWC'), ('natural', 'Natural')], string='Top Paper Color', tracking=True)
    bottom_liner_color = fields.Selection([('golden', 'Golden'), ('lwc', 'LWC'), ('natural', 'Natural')], string='Bottom Liner Color', tracking=True)
    top_liner_color = fields.Selection([('golden', 'Golden'), ('lwc', 'LWC'), ('natural', 'Natural')], string='Top Liner Color', tracking=True)
    top_weight = fields.Float(string="Top Weight", tracking=True)
    bottom_weight = fields.Float(string="Bottom Weight", tracking=True)
    lwc_weight = fields.Float(string="Top Weight", tracking=True)
    per_box_weight = fields.Float(string="Per Box Weight", tracking=True)
    total_weight = fields.Float(string="Total Weight", tracking=True)
    total_lwc_weight = fields.Float(string="Total Top Weight", tracking=True)
    total_natural_weight = fields.Float(string="Total Liner Weight", tracking=True)
    box_per_sheet = fields.Float(string='Box Per Sheet', tracking=True)

    @api.depends('company_name', 'product_name', 'order_no')
    def _compute_full_description(self):
        for rec in self:
            rec.full_description = (
                f"{rec.company_name.name or ''}"
                f" - {rec.product_name or ''} ({rec.order_no or ''})")

    @api.model_create_multi
    def create(self, vals_list):
        """Override create() to assign sequence automatically."""
        for vals in vals_list:
            if vals.get('order_no', 'New') == 'New':
                vals['order_no'] = self.env['ir.sequence'].next_by_code('parffoma.order') or 'New'
        return super(ParffomaOrder, self).create(vals_list)

    # ✅ Validation: only allow digits and "/"
    @api.constrains('b_value', 'h_value', 'l_value', 'f_value')
    def _check_dimension_values(self):
        pattern = re.compile(r'^[0-9/]*$')
        for rec in self:
            for field_name in ['b_value', 'h_value', 'l_value', 'f_value']:
                value = getattr(rec, field_name)
                if value and not pattern.match(value):
                    raise ValidationError(_("Field '%s' may only contain numbers"
                                            " and '/' (e.g., 70, 70/75). Invalid value: %s"
                    ) % (field_name.upper(), value))

    # ✅ Validation: only allow digits and "/"
    @api.onchange('b_value', 'h_value', 'l_value', 'f_value')
    def _onchange_dimension_values(self):
        pattern = re.compile(r'^[0-9/]*$')
        for rec in self:
            for field_name in ['b_value', 'h_value', 'l_value', 'f_value']:
                value = getattr(rec, field_name)
                if value and not pattern.match(value):
                    raise ValidationError(_("Field '%s' may only contain numbers and"
                                            " '/' (e.g., 70, 70/75). Invalid value: %s"
                    ) % (field_name.upper(), value))

    @api.depends('order_no')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"Order {rec.order_no}"

    @api.onchange('paper_id', 'box_per_sheet', 'box_qty')
    def _onchange_paper_id(self):
        for rec in self:
            if rec.paper_id and self.env.context.get('update_paper_details', False):
                rec.box_per_sheet = rec.paper_id.box_per_sheet
                rec.paper_decal = rec.paper_id.paper_decal
                rec.paper_cutting = rec.paper_id.paper_cutting
                rec.top_paper_gsm = rec.paper_id.top_paper_gsm
                rec.top_liner_gsm = rec.paper_id.top_liner_gsm
                rec.bottom_liner_gsm = rec.paper_id.bottom_liner_gsm
                rec.top_paper_color = rec.paper_id.top_paper_color
                rec.top_liner_color = rec.paper_id.top_liner_color
                rec.bottom_liner_color = rec.paper_id.bottom_liner_color
            rec.top_paper_qty = rec.box_qty / rec.box_per_sheet
            rec.top_liner_qty = rec.box_qty / rec.box_per_sheet
            rec.bottom_liner_qty = rec.box_qty / rec.box_per_sheet


    @api.onchange('paper_decal', 'paper_cutting', 'top_paper_gsm', 'bottom_liner_gsm', 'box_qty', 'box_per_sheet', 'top_paper_qty', 'bottom_liner_qty')
    def _onchange_paper_details(self):
        for rec in self:
            if rec.paper_id:
                temp_weight = rec.paper_decal * rec.paper_cutting / rec.paper_id.formula
                rec.lwc_weight = temp_weight * float(rec.paper_id.top_paper_gsm.split('/')[0]) if rec.paper_id.top_paper_gsm else 0
                rec.bottom_weight = temp_weight  * float(rec.paper_id.bottom_liner_gsm.split('/')[0]) if rec.paper_id.bottom_liner_gsm else 0
                rec.top_weight = temp_weight  * float(rec.paper_id.top_liner_gsm.split('/')[0]) * 1.4 if rec.paper_id.top_liner_gsm else 0
                rec.per_box_weight = (rec.lwc_weight + rec.top_weight + rec.bottom_weight) / rec.box_per_sheet
                rec.total_lwc_weight = rec.lwc_weight * rec.top_paper_qty / 1000
                rec.total_natural_weight = (rec.bottom_weight+ rec.top_weight) * rec.bottom_liner_qty / 1000
                rec.total_weight = rec.per_box_weight * rec.box_qty / 1000
