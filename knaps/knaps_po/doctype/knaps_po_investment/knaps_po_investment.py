import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, formatdate, getdate

from knaps.utils.constants import DOCTYPE_PO_INVESTMENT
from knaps.utils.investment import (
	clear_maturity_if_no_start_date,
	set_primary_client,
	validate_account_number_for_active,
	validate_amount,
	validate_holders_by_holding_type,
	validate_minor_holder,
	validate_no_dates_for_entry_status,
	validate_nominees,
	validate_rate_of_interest,
	validate_start_date_with_account,
	validate_unique_holders,
)
from knaps.utils.investment import (
	set_maturity_date as set_base_maturity_date,
)
from knaps.utils.shared import (
	generate_investment_name,
	set_nominee_minor_status,
	validate_entry_date_not_future,
	validate_nominee_minor_guardian,
	validate_nominee_not_holder,
	validate_nominee_percent_total,
	validate_payments_required,
	validate_period_in_months,
	validate_unique_nominees,
)


class KNAPSPOInvestment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_payment.knaps_payment import KNAPSPayment
		from knaps.knaps_client_management.doctype.knaps_holder.knaps_holder import KNAPSHolder
		from knaps.knaps_client_management.doctype.knaps_nominee.knaps_nominee import KNAPSNominee
		from knaps.knaps_po.doctype.knaps_po_extension.knaps_po_extension import KNAPSPOExtension

		account_number: DF.Data | None
		amount: DF.Currency
		client_name: DF.Data | None
		currency: DF.Link | None
		entry_date: DF.Date
		extend_investment: DF.Check
		extensions: DF.Table[KNAPSPOExtension]
		holders: DF.Table[KNAPSHolder]
		holding_type: DF.Link
		is_existing_investment: DF.Check
		maturity_date: DF.Date | None
		nominees: DF.Table[KNAPSNominee]
		partner: DF.Link | None
		passbook_status: DF.Literal["Not Created", "With Us", "With Client", "With PO"]
		payments: DF.Table[KNAPSPayment]
		period_in_months: DF.Int
		po_branch: DF.Data | None
		primary_client: DF.Link | None
		rate_of_interest: DF.Float
		scheme_code: DF.Data | None
		scheme_name: DF.Link
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
		through_partner: DF.Check
		through_us: DF.Check
		title: DF.Data | None
	# end: auto-generated types

	def autoname(self) -> None:
		self.name = generate_investment_name(DOCTYPE_PO_INVESTMENT, "KNAPS-PO-", self.entry_date)

	def before_validate(self) -> None:
		set_nominee_minor_status(self)

	def before_save(self) -> None:
		clear_maturity_if_no_start_date(self)
		set_primary_client(self)
		self._set_title()
		self._set_maturity_date()

	def validate(self) -> None:
		validate_unique_holders(self)
		validate_minor_holder(self)
		validate_holders_by_holding_type(self)
		validate_nominee_not_holder(self)
		validate_unique_nominees(self)
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_nominees(self)
		if not self.is_existing_investment:
			validate_payments_required(self)
		validate_entry_date_not_future(self)
		validate_no_dates_for_entry_status(self)
		validate_account_number_for_active(self)
		validate_start_date_with_account(self)
		validate_amount(self)
		validate_rate_of_interest(self)
		validate_period_in_months(self)
		self._validate_extension_sequence()

	def _set_title(self) -> None:
		if self.client_name and self.scheme_code:
			self.title = f"{self.client_name} - {self.scheme_code}"

	def _set_maturity_date(self) -> None:
		if self.extend_investment and self.get("extensions"):
			extensions = self.get("extensions")
			last_ext = extensions[-1]
			if last_ext.extension_date and last_ext.extension_period:
				self.maturity_date = add_months(
					getdate(last_ext.extension_date),
					last_ext.extension_period,
				)
				return
		set_base_maturity_date(self)

	def _validate_extension_sequence(self) -> None:
		extensions = self.get("extensions")
		if not extensions:
			return

		if not self.extend_investment:
			frappe.throw(
				_("Extensions can only be added when Extend Investment is checked."),
				title=_("Invalid Extension"),
			)

		if not self.start_date:
			return

		original_maturity = add_months(getdate(self.start_date), self.period_in_months)

		for i, ext in enumerate(extensions):
			self._validate_single_extension(i, ext, extensions, original_maturity)

	def _validate_single_extension(self, i: int, ext, extensions: list, original_maturity) -> None:
		ext_num = ext.idx

		if ext.extension_period <= 0:
			frappe.throw(
				_("Extension #{}: Extension period must be positive.").format(ext_num),
				title=_("Invalid Extension Period"),
			)

		if i == 0:
			reference = original_maturity
			msg = _("Extension #{}: Date must be on or after the maturity date {}.").format(
				ext_num, formatdate(original_maturity, "dd-mm-yyyy")
			)
		else:
			prev = extensions[i - 1]
			reference = add_months(getdate(prev.extension_date), prev.extension_period)
			msg = _("Extension #{}: Date must be on or after the previous maturity date {}.").format(
				ext_num, formatdate(reference, "dd-mm-yyyy")
			)

		if getdate(ext.extension_date) < getdate(reference):
			frappe.throw(msg, title=_("Invalid Extension Date"))
