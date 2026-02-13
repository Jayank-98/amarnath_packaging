# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PrintingNote(models.Model):
    """ This model represents printing.note."""
    _name = 'printing.note'
    _description = 'Printing Note'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(default=True, string='Active')
