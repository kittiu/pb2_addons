# -*- coding: utf-8 -*-
{
    "name": "NSTDA :: PABI2 - Source Document",
    "summary": "",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "description": """
It stores very first origin document reference on invoice.
    """,
    "website": "https://ecosoft.co.th/",
    "author": "Kitti U.",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        'account',
        'sale',
        'purchase',
        'hr_expense_auto_invoice',
    ],
    "data": [
        'views/account_invoice_view.xml',
    ],
}
