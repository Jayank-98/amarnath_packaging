from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re


class PaperType(models.Model):
    _name = 'paper.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Paper Type'

    name = fields.Char(string="Paper Type", required=True, tracking=True)
    paper_decal = fields.Float(string='Paper Decal', tracking=True)
    paper_cutting = fields.Float(string='Paper Cutting', tracking=True)

    top_paper_gsm = fields.Char(string='Top Paper GSM/BF', tracking=True)
    top_paper_color = fields.Selection([('golden', 'Golden'), ('lwc', 'LWC'), ('natural', 'Natural')], string='Top Paper Color', tracking=True)

    top_liner_gsm = fields.Char(string='Top Liner GSM/BF', tracking=True)
    bottom_liner_gsm = fields.Char(string='Bottom Liner GSM/BF', tracking=True)
    bottom_liner_color = fields.Selection([('golden', 'Golden'), ('lwc', 'LWC'), ('natural', 'Natural')], string='Bottom Liner Color', tracking=True)
    top_liner_color = fields.Selection([('golden', 'Golden'), ('lwc', 'LWC'), ('natural', 'Natural')], string='Top Liner Color', tracking=True)

    box_per_sheet = fields.Float(string='Box/Sheet', tracking=True)
    formula = fields.Float(string='Formula', default=1550.00, tracking=True)

    @api.constrains('bottom_liner_gsm', 'top_paper_gsm')
    def _check_dimension_values(self):
        pattern = re.compile(r'^[0-9/]*$')
        for rec in self:
            for field_name in ['bottom_liner_gsm', 'top_paper_gsm']:
                value = getattr(rec, field_name)
                if value and not pattern.match(value):
                    raise ValidationError(_("Field '%s' may only contain numbers"
                                            " and '/' (e.g., 70, 70/75). Invalid value: %s"
                    ) % (field_name.upper(), value))

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} --D-{rec.paper_decal} PC-{rec.paper_cutting} TOP-{rec.top_paper_gsm} BOTTOM-{rec.bottom_liner_gsm}--"
