from odoo import models, fields, api
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class DispatchHistoryWizard(models.TransientModel):
    _name = 'dispatch.history.wizard'
    _description = 'Dispatch History PDF Wizard'

    process_order_id = fields.Many2one('process.order')

    date_range_type = fields.Selection([
        ('1', 'Last 1 Month'),
        ('2', 'Last 2 Months'),
        ('3', 'Last 3 Months'),
        ('custom', 'Custom')
    ], default='1', required=True)

    start_date = fields.Date()
    end_date = fields.Date()

    @api.onchange('date_range_type')
    def _onchange_date_range_type(self):
        today = date.today()

        if self.date_range_type in ['1', '2', '3']:
            months = int(self.date_range_type)
            self.end_date = today
            self.start_date = today - relativedelta(months=months)

    def action_generate_pdf(self):
        return self.env.ref(
            'jm_delivery_challan.dispatch_history_pdf_report'
        ).report_action(self)
