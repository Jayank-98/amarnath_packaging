# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.addons.account.models.company import PEPPOL_LIST


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    manufacturing_type = fields.Selection([
        ('single_liner', 'Single Liner'),
        ('double_liner', 'Double Liner'),
        ('both', 'Both')], string='Manufacturing Type')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('jm_parformma_custom.manufacturing_type', self.manufacturing_type)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['manufacturing_type'] = get_param('jm_parformma_custom.manufacturing_type')
        return res
