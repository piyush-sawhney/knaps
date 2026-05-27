import frappe
from frappe import _
from frappe.model.document import Document


class KNAPSRDSchedule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps_po.doctype.knaps_rd_transaction.knaps_rd_transaction import KNAPSRDTransaction

		amended_from: DF.Link | None
		deposit_amount: DF.Float
		rd_accounts: DF.Table[KNAPSRDTransaction]
		schedule_amount: DF.Float
		schedule_date: DF.Date | None
		schedule_document: DF.Attach | None
		schedule_number: DF.Data | None
		schedule_type: DF.Literal["Cash", "Cheque"]
		total_rebate: DF.Float
		total_surcharge: DF.Float
	# end: auto-generated types

	def before_validate(self) -> None:
		if self.is_new():
			self.schedule_number = None
			self.schedule_date = None
			self.total_rebate = 0.0
			self.total_surcharge = 0.0
			self.deposit_amount = 0.0
			self.schedule_document = None

	def validate(self) -> None:
		self._validate_bank_account_number()
		if self.rd_accounts:
			self._validate_duplicate_accounts()
			for row in self.rd_accounts:
				self._validate_schedule_type_fields(row)

	def before_save(self) -> None:
		self._reset_financials()
		if self.rd_accounts:
			for row in self.rd_accounts:
				self._accumulate_row_financials(row)

	def _validate_bank_account_number(self) -> None:
		if self.schedule_type and self.schedule_type.lower() == "cheque":
			if self.rd_accounts:
				for row in self.rd_accounts:
					if not row.bank_account_number or len(row.bank_account_number) < 5:
						frappe.throw(
							_("Invalid bank account number for account {}.").format(row.rd_account_number),
							title=_("Bank Account Error"),
						)

	def _reset_financials(self) -> None:
		self.total_rebate = 0.0
		self.total_surcharge = 0.0
		self.schedule_amount = 0.0
		self.deposit_amount = 0.0

	def _validate_duplicate_accounts(self) -> None:
		account_list: list[str] = []
		for row in self.rd_accounts or []:
			if row.rd_account_number in account_list:
				frappe.throw(
					_("Duplicate Account Number: {}.").format(row.rd_account_number),
					title=_("Duplicate Account"),
				)
			account_list.append(row.rd_account_number)

	def _validate_schedule_type_fields(self, row) -> None:
		if self.schedule_type and self.schedule_type.lower() == "cash":
			if row.cheque_number:
				frappe.throw(
					_("Cannot have cheque number for account {} in a cash schedule.").format(
						row.rd_account_number
					),
					title=_("Cash Schedule Error"),
				)
			row.bank_account_number = None
		elif self.schedule_type and self.schedule_type.lower() == "cheque":
			if not row.cheque_number or len(row.cheque_number) != 6:
				frappe.throw(
					_("Invalid cheque number for account {}.").format(row.rd_account_number),
					title=_("Cheque Number Error"),
				)
		else:
			frappe.throw(
				_("Invalid schedule type."),
				title=_("Schedule Type Error"),
			)

	def _accumulate_row_financials(self, row) -> None:
		if row.denomination and row.number_of_installments:
			row.rd_amount = row.denomination * row.number_of_installments
			self.schedule_amount += row.rd_amount
			row.rd_deposit_amount = row.rd_amount
			if row.rebate:
				row.rd_deposit_amount -= row.rebate
				self.total_rebate += row.rebate
			if row.surcharge:
				row.rd_deposit_amount += row.surcharge
				self.total_surcharge += row.surcharge
			self.deposit_amount += row.rd_deposit_amount
