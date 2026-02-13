# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    """ This model represents res.users."""
    _inherit = 'res.users'

    report_sign = fields.Binary(string='Signature for Reports')
