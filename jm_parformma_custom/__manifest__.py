# -*- coding: utf-8 -*-
{
    'name': 'JM Parformma Custom',
    'version': '1.0',
    'summary': 'Manage Parffoma Orders for box manufacturing',
    'description': '''
        Custom module to manage Parffoma Orders including sizes, printing, papers, etc.
    ''',
    'category': 'Aarooha Tech Labs',
    'author': 'Jayank M Aghara',
    'company': 'Aarooha Tech Labs',
    'maintainer': 'Aarooha Tech Labs',
    'depends': ['base', 'mail'],
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
		'report/parfomma_report.xml',
        'views/jm_parformma_custom_views.xml',
		'views/res_partner_views.xml',
		'views/paper_type_views.xml',
],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
