# -*- encoding: utf-8 -*-
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_invoice(self, order, lines):
        invoice_vals = super(SaleOrder, self)._prepare_invoice(order, lines)
        workflow = order.workflow_process_id
        if not workflow:
            return invoice_vals
        invoice_vals['number_preprint'] = order.origin
        return invoice_vals

    @api.onchange('workflow_process_id')
    def onchange_workflow_process_id(self):
        if not self.workflow_process_id:
            return
        workflow = self.workflow_process_id
        if workflow.operating_unit_id:
            self.operating_unit_id = workflow.operating_unit_id
        return super(SaleOrder, self).onchange_workflow_process_id()

    @api.model
    def default_get(self, field_list):
        res = super(SaleOrder, self).default_get(field_list)
        process_id = self._context.get('default_workflow_process_id', False)
        if process_id:
            process = self.env['sale.workflow.process'].browse(process_id)
            res['taxbranch_id'] = process.taxbranch_id.id
        return res

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for order in self.filtered('workflow_process_id'):
            pickings = order.picking_ids.\
                filtered('workflow_process_id.validate_picking')
            pickings.validate_picking()
            order.filtered(lambda l: l.invoiced and l.shipped).action_done()
        return res

    @api.multi
    def action_invoice_create(self):
        res = super(SaleOrder, self).action_invoice_create()
        invoices = self.env['account.invoice'].browse(res)
        for invoice in invoices:
            if invoice.workflow_process_id.validate_invoice:
                invoice.signal_workflow('invoice_open')
                # Validate payment too
                journal = invoice.workflow_process_id.voucher_journal_id
                bank = invoice.workflow_process_id.partner_bank_id
                voucher = self._auto_validate_payment(invoice, journal)
                self._auto_validate_bank_receipt(voucher, journal, bank)
        return res

    @api.model
    def _auto_validate_payment(self, invoice, journal):
        # Create Payment and Validate It!
        voucher = self.env['account.voucher'].create({
            'date': fields.Date.context_today(self),
            'amount': invoice.amount_total,
            'account_id': journal.default_debit_account_id.id,
            'partner_id': invoice.partner_id.id,
            'type': 'receipt',
            'date_value': fields.Date.context_today(self),
            'journal_id': journal.id,
            'operating_unit_id': invoice.operating_unit_id.id,
        })
        val = voucher.\
            with_context({
                'filter_invoices': [invoice.id]}).\
            onchange_partner_id(
                voucher.partner_id.id,
                voucher.journal_id.id,
                voucher.amount,
                voucher.currency_id.id,
                voucher.type,
                voucher.date
            )
        voucher_lines = [(0, 0, line) for
                         line in val['value']['line_cr_ids']]
        voucher.write({'line_cr_ids': voucher_lines})
        if not voucher.writeoff_amount:
            voucher.signal_workflow('proforma_voucher')
        return voucher

    @api.model
    def _auto_validate_bank_receipt(self, voucher, journal, bank):
        move_lines = voucher.move_ids.filtered(
            lambda l:
            l.account_id == journal.default_debit_account_id and
            l.debit > 0.0 and
            not l.reconcile_id
        )
        total_amount = sum(move_lines.mapped('debit'))
        # Create Bank Receipt and Validate it
        receipt = self.env['account.bank.receipt'].create({
            'date': fields.Date.context_today(self),
            'journal_id': journal.id,
            'currency_id':
            journal.currency.id or journal.company_id.currency_id.id,
            'partner_bank_id': bank.id,
            'bank_account_id': bank.journal_id.default_debit_account_id.id,
            'manual_total_amount': total_amount,
            'total_amount': total_amount,
            'bank_intransit_ids': [(6, 0, move_lines.ids)],
        })
        receipt.validate_bank_receipt()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def default_get(self, field_list):
        res = super(SaleOrderLine, self).default_get(field_list)
        process_id = self._context.get('workflow_process_id', False)
        if process_id:
            process = self.env['sale.workflow.process'].browse(process_id)
            res['section_id'] = process.res_section_id.id
        return res
