# -*- coding: utf-8 -*-
# © <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    advance_move_line_id = fields.Many2one(
        'account.move.line',
        'Expense Advance Journal Item',
        readonly=True,
        copy=False,
    )

    @api.model
    def _get_invoice_total(self, invoice):
        amount_total = super(AccountInvoice, self)._get_invoice_total(invoice)
        return amount_total - self._prev_advance_amount(invoice)

    @api.model
    def _prev_advance_amount(self, invoice):
        advance_product = self.env.ref('hr_expense_advance_clearing.'
                                       'product_product_employee_advance')
        lines = invoice.invoice_line
        # Advance with Negative Amount
        advance_lines = lines.filtered(lambda x: x.price_subtotal < 0 and
                                       x.product_id == advance_product)
        return sum([l.price_subtotal for l in advance_lines])

    @api.multi
    def invoice_validate(self):
        result = super(AccountInvoice, self).invoice_validate()
        for invoice in self:
            if invoice.advance_move_line_id:
                advance_move_line = invoice.advance_move_line_id
                move_lines = invoice.move_id.line_id
                move_line_to_reconcile = advance_move_line
                move_line =\
                    move_lines.filtered(
                        lambda x: x.account_id.reconcile is True and
                        x.account_id.type == 'other')
                move_line_to_reconcile += move_line
                move_line_to_reconcile.reconcile_partial(type='manual')
        return result
