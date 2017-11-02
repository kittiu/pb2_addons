# -*- coding: utf-8 -*-
from openerp import fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    loan_installment_account_id = fields.Many2one(
        'account.account',
        string='Loan Installment Account',
        related="company_id.loan_installment_account_id",
    )
    loan_defer_income_account_id = fields.Many2one(
        'account.account',
        string='Defer Income Account',
        related="company_id.loan_defer_income_account_id",
    )
    loan_income_account_id = fields.Many2one(
        'account.account',
        string='Income Account',
        related="company_id.loan_income_account_id",
    )