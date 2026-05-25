from datetime import date

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from knaps.utils.investment import (
	build_nominee_name_cache,
	set_maturity_date,
	set_nominee_minor_status,
	set_primary_client,
	validate_account_number_for_active,
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


class KNAPSFixedInvestment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_payment.knaps_payment import KNAPSPayment
		from knaps.knaps_client_management.doctype.knaps_holder.knaps_holder import KNAPSHolder
		from knaps.knaps_client_management.doctype.knaps_nominee.knaps_nominee import KNAPSNominee

		account_number: DF.Data | None
		amount: DF.Currency
		broker_details: DF.Link | None
		client_name: DF.Data | None
		currency: DF.Link | None
		entry_date: DF.Date
		holders: DF.Table[KNAPSHolder]
		holding_mode: DF.Literal["Physical", "Demat"]
		holding_type: DF.Link
		investment_company: DF.Link
		investment_mode: DF.Literal["", "Monthly", "Quarterly", "Half-Yearly", "Yearly", "Cummulative"]
		investment_type: DF.Literal["FD- Fixed Deposit", "NCD - Non Convertible Debentures", "BOND"]
		is_existing_investment: DF.Check
		maturity_date: DF.Date | None
		nominees: DF.Table[KNAPSNominee]
		partner: DF.Link | None
		passbook_status: DF.Literal["Not Created", "With Us", "With Client", "With Company"]
		payments: DF.Table[KNAPSPayment]
		period_in_months: DF.Int
		primary_client: DF.Link | None
		rate_of_interest: DF.Float
		scheme_name: DF.Data | None
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
		through_broker: DF.Check
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

		prefix = f"KNAPS-FI-{ty_start % 100:02d}-{ty_end % 100:02d}-"

		last_serial = 0
		last = frappe.db.get_value(
			"KNAPS Fixed Investment",
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
		set_maturity_date(self)

	def validate(self) -> None:
		self._nominee_name_cache = build_nominee_name_cache(self)
		validate_unique_holders(self)
		validate_minor_holder(self)
		validate_holders_by_holding_type(self, enforce_single_for_non_individual=True)
		validate_nominee_not_holder(self)
		validate_unique_nominees(self)
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_nominees(self, nominees_optional_for_non_individual=True)
		validate_payments(self)
		validate_entry_date_not_future(self)
		validate_no_dates_for_entry_status(self)
		validate_account_number_for_active(self)
		validate_start_date_with_account(self)
		validate_amount(self)
		validate_rate_of_interest(self)
		validate_period_in_months(self)

	def _set_title(self) -> None:
		if self.client_name and self.investment_type:
			code = self.investment_type.split(" -")[0].split("- ")[0].strip()
			self.title = f"{self.client_name} - {code}"
