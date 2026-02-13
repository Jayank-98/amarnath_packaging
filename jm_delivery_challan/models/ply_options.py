# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PlyOptions(models.Model):
    """ This model represents ply.options."""
    _name = 'ply.options'
    _description = 'Ply Options'

    name = fields.Char(string='Ply Option', required=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals):
        """Override the default create method to customize record creation logic."""
        return super().create(vals)