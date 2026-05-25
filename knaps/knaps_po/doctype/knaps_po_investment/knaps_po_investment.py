from datetime import date

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, formatdate, getdate

from knaps.utils.investment import (
	build_nominee_name_cache,
	set_nominee_minor_status,
	set_primary_client,
	validate_amount,
	validate_entry_date_not_future,
	validate_holders_by_holding_type,
	validate_minor_holder,
	validate_no_dates_for_entry_status,
	validate_nominee_minor_guardian,
	validate_nominee_not_holder,
	validate_nominee_percent_total,
	validate_nominees,
	validate_payments,
	validate_period_in_months,
	validate_rate_of_interest,
	validate_start_date_with_account,
	validate_unique_holders,
	validate_unique_nominees,
)
from knaps.utils.investment import (
	set_maturity_date as set_base_maturity_date,
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
		entry_date = self.entry_date or date.today()
		if isinstance(entry_date, str):
			entry_date = getdate(entry_date)

		if entry_date.month >= 4:
			ty_start = entry_date.year
			ty_end = entry_date.year + 1
		else:
			ty_start = entry_date.year - 1
			ty_end = entry_date.year

		prefix = f"KNAPS-PO-{ty_start % 100:02d}-{ty_end % 100:02d}-"

		last_serial = 0
		last = frappe.db.get_value(
			"KNAPS PO Investment",
			{"name": ["like", f"{prefix}%"]},
			"name",
			order_by="name desc",
		)
		if last:
			last_serial = int(last.split("-")[-1])

		self.name = f"{prefix}{last_serial + 1:08d}"

	def before_validate(self) -> None:
		set_nominee_minor_status(self)

	def before_save(self) -> None:
		set_primary_client(self)
		self._set_title()
		self._set_maturity_date()

	def validate(self) -> None:
		self._nominee_name_cache = build_nominee_name_cache(self)
		validate_unique_holders(self)
		validate_minor_holder(self)
		validate_holders_by_holding_type(self)
		validate_nominee_not_holder(self)
		validate_unique_nominees(self)
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_nominees(self)
		validate_payments(self)
		validate_entry_date_not_future(self)
		validate_no_dates_for_entry_status(self)
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
			ext_num = ext.idx

			if ext.extension_period <= 0:
				frappe.throw(
					_("Extension #{}: Extension period must be positive.").format(ext_num),
					title=_("Invalid Extension Period"),
				)

			if i == 0:
				if getdate(ext.extension_date) < getdate(original_maturity):
					frappe.throw(
						_("Extension #{}: Date must be on or after the maturity date {}.").format(
							ext_num, formatdate(original_maturity, "dd-mm-yyyy")
						),
						title=_("Invalid Extension Date"),
					)
			else:
				prev = extensions[i - 1]
				prev_maturity = add_months(getdate(prev.extension_date), prev.extension_period)
				if getdate(ext.extension_date) < getdate(prev_maturity):
					frappe.throw(
						_("Extension #{}: Date must be on or after the previous maturity date {}.").format(
							ext_num, formatdate(prev_maturity, "dd-mm-yyyy")
						),
						title=_("Invalid Extension Date"),
					)
