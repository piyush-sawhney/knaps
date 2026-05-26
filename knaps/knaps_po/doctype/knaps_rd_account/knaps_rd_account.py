import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class KNAPSRDAccount(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_number: DF.Data | None
		account_opening_date: DF.Date | None
		amount: DF.Currency
		bank: DF.Link | None
		bank_account_number: DF.Data | None
		card_number: DF.Data | None
		client_name: DF.Data | None
		currency: DF.Link | None
		default_fee: DF.Currency
		default_installments: DF.Int
		denomination: DF.Currency
		effective_card_number: DF.Data | None
		extension_card_number: DF.Data | None
		holder_name: DF.Data | None
		is_updated: DF.Check
		last_deposit_date: DF.Date | None
		last_updated: DF.Datetime | None
		next_installment_date: DF.Date | None
		pending_installments: DF.Int
		po_rd_investment: DF.Link | None
		rd_account_number: DF.Data
		rebate: DF.Currency
		start_date: DF.Date | None
		status: DF.Literal[
			"Entry Done",
			"Submitted",
			"Active",
			"Renewed",
			"Matured",
			"Pre-Matured",
			"Transmitted",
			"Rejected",
		]
		title: DF.Data | None
		total_deposit_amount: DF.Currency
		total_months_paid: DF.Int
	# end: auto-generated types

	def before_save(self) -> None:
		self._set_title()
		self._set_effective_card_number()

	def validate(self) -> None:
		self._validate_account_number_match()
		self._validate_denomination_match()
		self._validate_start_date_match()

	def _set_title(self) -> None:
		if self.client_name and self.rd_account_number:
			suffix = (
				self.rd_account_number[-4:] if len(self.rd_account_number) >= 4 else self.rd_account_number
			)
			self.title = f"{self.client_name}-RD-{suffix}"
		elif self.client_name:
			self.title = f"{self.client_name}-RD"

	def _set_effective_card_number(self) -> None:
		self.effective_card_number = self.extension_card_number or self.card_number
		self.is_updated = 1 if self.effective_card_number else 0

	def _validate_account_number_match(self) -> None:
		if not self.po_rd_investment or not self.rd_account_number:
			return
		po_account = frappe.db.get_value("KNAPS PO Investment", self.po_rd_investment, "account_number")
		if po_account and self.rd_account_number != po_account:
			frappe.throw(
				_("RD Account Number {} does not match PO Investment account number {}.").format(
					self.rd_account_number, po_account
				),
				title=_("Account Mismatch"),
			)

	def _validate_denomination_match(self) -> None:
		if not self.po_rd_investment or not self.denomination:
			return
		po_amount = frappe.db.get_value("KNAPS PO Investment", self.po_rd_investment, "amount")
		if po_amount and self.denomination != po_amount:
			frappe.throw(
				_("Denomination {} does not match PO Investment amount {}.").format(
					self.denomination, po_amount
				),
				title=_("Denomination Mismatch"),
			)

	def _validate_start_date_match(self) -> None:
		if not self.po_rd_investment or not self.account_opening_date:
			return
		po_start = frappe.db.get_value("KNAPS PO Investment", self.po_rd_investment, "start_date")
		if po_start and getdate(self.account_opening_date) != getdate(po_start):
			frappe.throw(
				_("Account Opening Date {} does not match PO Investment start date {}.").format(
					self.account_opening_date, po_start
				),
				title=_("Date Mismatch"),
			)
