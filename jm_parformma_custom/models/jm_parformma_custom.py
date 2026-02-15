# jm_custom_parffoma/models/parffoma_order.py
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re

def _parse_gsm_value(gsm):
    """Extract numeric GSM value from string like '230/10' safely."""
    if not gsm:
        return 0.0
    try:
        return float(str(gsm).split('/')[0])
    except (ValueError, IndexError):
        return 0.0


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
    product_id = fields.Many2one("product.product", string='Product', tracking=True)
    printing = fields.Char(string='Printing', tracking=True)
    printing_note_id = fields.Many2one('printing.note', string='Printing Note', tracking=True)
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
    ply_option_id = fields.Many2one("ply.options", string='Ply Options')

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
    print_weight = fields.Boolean(string='Print Weight', tracking=True)
    manufacturing_type = fields.Selection([
        ('single_liner', 'Single Liner'),
        ('double_liner', 'Double Liner'),
        ('both', 'Both')], string='Manufacturing Type')

    @api.model
    def default_get(self, fields):
        """If we're creating a new account through a many2one, there are chances that we typed the account code
        instead of its name. In that case, switch both fields values.
        """

        defaults = super(ParffomaOrder, self).default_get(fields)
        if 'manufacturing_type' in fields:
           default_manufacturing_type = self.env['ir.config_parameter'].sudo().get_param('jm_parformma_custom.manufacturing_type')
           defaults['manufacturing_type'] = default_manufacturing_type
        return defaults

    @api.depends('company_name', 'product_id', 'order_no')
    def _compute_full_description(self):
        for rec in self:
            rec.full_description = (
                f"{rec.company_name.name or ''}"
                f" - {rec.product_id.name if rec.product_id else ''} ({rec.order_no or ''})")

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
    @api.onchange('b_value', 'h_value', 'l_value', 'f_value', 'top_paper_gsm', 'top_liner_gsm', 'bottom_liner_gsm')
    def _onchange_dimension_values(self):
        pattern = re.compile(r'^[0-9/]*$')
        for rec in self:
            for field_name in ['b_value', 'h_value', 'l_value', 'f_value', 'top_paper_gsm', 'top_liner_gsm', 'bottom_liner_gsm']:
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
            paper = rec.paper_id

            # Populate paper details from master
            if paper and self.env.context.get('update_paper_details'):
                rec.update({
                    'box_per_sheet': paper.box_per_sheet,
                    'paper_decal': paper.paper_decal,
                    'paper_cutting': paper.paper_cutting,
                    'top_paper_gsm': paper.top_paper_gsm,
                    'top_liner_gsm': paper.top_liner_gsm,
                    'bottom_liner_gsm': paper.bottom_liner_gsm,
                    'top_paper_color': paper.top_paper_color,
                    'top_liner_color': paper.top_liner_color,
                    'bottom_liner_color': paper.bottom_liner_color,
                })

            # Quantity calculation with safety
            box_per_sheet = rec.box_per_sheet or 0
            box_qty = rec.box_qty or 0

            if box_per_sheet:
                qty = box_qty / box_per_sheet
            else:
                qty = 0

            rec.top_paper_qty = qty
            rec.top_liner_qty = qty
            rec.bottom_liner_qty = qty

    @api.onchange(
        'paper_decal', 'paper_cutting',
        'top_paper_gsm', 'bottom_liner_gsm', 'top_liner_gsm',
        'box_qty', 'box_per_sheet',
        'top_paper_qty', 'bottom_liner_qty', 'top_liner_qty'
    )
    def _onchange_paper_details(self):
        for rec in self:
            paper = rec.paper_id
            if not paper:
                pass

            try:
                # Safe base values
                paper_decal = rec.paper_decal or 0
                paper_cutting = rec.paper_cutting or 0
                formula = paper.formula or 1  # avoid division by zero
                box_per_sheet = rec.box_per_sheet or 0
                box_qty = rec.box_qty or 0

                top_qty = rec.top_paper_qty or 0
                top_liner_qty = rec.top_liner_qty or 0
                bottom_qty = rec.bottom_liner_qty or 0

                # GSM numeric extraction
                top_paper_gsm = _parse_gsm_value(rec.top_paper_gsm)
                bottom_liner_gsm = _parse_gsm_value(rec.bottom_liner_gsm)
                top_liner_gsm = _parse_gsm_value(rec.top_liner_gsm)

                # Base weight
                temp_weight = (paper_decal * paper_cutting) / formula if formula else 0

                # Weight calculations
                rec.lwc_weight = temp_weight * top_paper_gsm if top_paper_gsm and top_qty else 0
                rec.bottom_weight = temp_weight * bottom_liner_gsm if bottom_liner_gsm and bottom_qty else 0
                rec.top_weight = temp_weight * top_liner_gsm * 1.4 if top_liner_qty and top_liner_gsm else 0

                total_weight_per_sheet = (
                        rec.lwc_weight + rec.top_weight + rec.bottom_weight
                )

                rec.per_box_weight = (
                    total_weight_per_sheet / box_per_sheet
                    if box_per_sheet else 0
                )

                rec.total_lwc_weight = (rec.lwc_weight * top_qty) / 1000
                rec.total_natural_weight =\
                    ((rec.bottom_weight + rec.top_weight) * max(bottom_qty, top_liner_qty)) / 1000
                rec.total_weight = (rec.per_box_weight * box_qty) / 1000

            except Exception:
                # Fail-safe reset (prevents UI crash)
                rec.update({
                    'lwc_weight': 0,
                    'bottom_weight': 0,
                    'top_weight': 0,
                    'per_box_weight': 0,
                    'total_lwc_weight': 0,
                    'total_natural_weight': 0,
                    'total_weight': 0,
                })
