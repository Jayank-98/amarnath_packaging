# -*- coding: utf-8 -*-
{
    'name': 'Jm Delivery Challan',
    'version': '19.0.1.0',
    'summary': 'Brief description of the module',
    'description': '''
        Detailed description of the module
    ''',
    'category': 'Uncategorized',
    'author': 'Jayank Aghara',
    'company': 'Aarooha Tech Labs',
    'maintainer': 'Jayank Aghara',
    'depends': ['base', 'jm_parformma_custom', 'sale_management', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/sale_order_sequence.xml',
        'data/server_action.xml',
        'views/sale_order_views.xml',
		'report/delivery_challan_action.xml',
		'report/dispatch_report.xml',
		'views/stock_picking_views.xml',
		'views/res_users_views.xml',
		'report/delivery_challan_template.xml',
		'views/process_order_views.xml',
		'wizard/process_order_wizard_views.xml',
		'wizard/dispatch_history_wizard_view.xml',
		'views/delivery_history_view.xml',
		'views/jm_parformma_order_views.xml',
],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}