from odoo import fields, models, api


class DispatchHistoryReport(models.AbstractModel):
    _name = 'report.jm_delivery_challan.dispatch_history_template'

    def _get_report_values(self, docids, data=None):
        wizard = self.env['dispatch.history.wizard'].browse(docids)
        process_order = wizard.process_order_id

        domain = [
            ('partner_id', '=', process_order.partner_id.id),
        ]

        if wizard.start_date:
            domain.append(('dispatch_date', '>=', wizard.start_date))
        if wizard.end_date:
            domain.append(('dispatch_date', '<=', wizard.end_date))

        dispatch_records = self.env['dispatch.history'].search(
            domain,
            order='dispatch_date desc'
        )

        return {
            'docs': dispatch_records,
            'process_order': process_order,
        }
