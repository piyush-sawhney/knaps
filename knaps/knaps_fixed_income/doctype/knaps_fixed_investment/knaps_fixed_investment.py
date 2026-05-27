import frappe
from frappe.model.document import Document

from knaps.utils.constants import DOCTYPE_FIXED_INVESTMENT
from knaps.utils.investment import (
	clear_maturity_if_no_start_date,
	set_maturity_date,
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
		self.name = generate_investment_name(DOCTYPE_FIXED_INVESTMENT, "KNAPS-FI-", self.entry_date)

	def before_validate(self) -> None:
		set_nominee_minor_status(self)

	def before_save(self) -> None:
		clear_maturity_if_no_start_date(self)
		set_primary_client(self)
		self._set_title()
		set_maturity_date(self)

	def validate(self) -> None:
		validate_unique_holders(self)
		validate_minor_holder(self)
		validate_holders_by_holding_type(self, enforce_single_for_non_individual=True)
		validate_nominee_not_holder(self)
		validate_unique_nominees(self)
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_nominees(self, nominees_optional_for_non_individual=True)
		if not self.is_existing_investment:
			validate_payments_required(self)
		validate_entry_date_not_future(self)
		validate_no_dates_for_entry_status(self)
		validate_account_number_for_active(self)
		validate_start_date_with_account(self)
		validate_amount(self)
		validate_rate_of_interest(self)
		validate_period_in_months(self)

	def _set_title(self) -> None:
		if self.client_name and self.investment_type:
			code = self.investment_type.split("-")[0].strip()
			self.title = f"{self.client_name} - {code}"
