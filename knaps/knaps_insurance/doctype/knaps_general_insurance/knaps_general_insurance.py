# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, add_years, getdate

from knaps.utils.constants import DOCTYPE_CLIENT, DOCTYPE_GENERAL_INSURANCE
from knaps.utils.insurance import (
	set_insurance_member_date_of_birth,
	set_primary_client,
	validate_member_minor_restrictions,
	validate_premium_positive,
	validate_start_date_before_maturity,
	validate_status_requirements,
	warn_missing_nominees,
)
from knaps.utils.shared import (
	generate_investment_name,
	set_nominee_minor_status,
	validate_entry_date_not_future,
	validate_nominee_minor_guardian,
	validate_nominee_percent_total,
	validate_payments_required,
	validate_unique_nominees,
)


class KNAPSGeneralInsurance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.core.doctype.dynamic_link.dynamic_link import DynamicLink
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_payment.knaps_payment import KNAPSPayment
		from knaps.knaps_client_management.doctype.knaps_nominee.knaps_nominee import KNAPSNominee
		from knaps.knaps_insurance.doctype.knaps_health_insurance_member.knaps_health_insurance_member import (
			KNAPSHealthInsuranceMember,
		)

		broker_details: DF.Link | None
		client_name: DF.Data | None
		currency: DF.Link | None
		entry_date: DF.Date
		has_multiple_members: DF.Check
		holders: DF.Table[KNAPSHealthInsuranceMember]
		insurance_plan_name: DF.Data | None
		investment_company: DF.Link
		is_existing_policy: DF.Check
		links: DF.Table[DynamicLink]
		maturity_date: DF.Date | None
		nominees: DF.Table[KNAPSNominee]
		partner: DF.Link | None
		payments: DF.Table[KNAPSPayment]
		period: DF.Int
		period_type: DF.Literal["", "Days", "Months", "Years"]
		policy_document: DF.Attach | None
		policy_number: DF.Data | None
		policy_type: DF.Link
		premium: DF.Currency
		primary_client: DF.Link | None
		quote_number: DF.Data | None
		start_date: DF.Date | None
		status: DF.Literal["Proposal", "Active", "Renewed", "Surrendered", "Rejected"]
		sum_assured: DF.Currency
		through_broker: DF.Check
		through_partner: DF.Check
		through_us: DF.Check
		title: DF.Data | None
	# end: auto-generated types

	def autoname(self) -> None:
		self.name = generate_investment_name(DOCTYPE_GENERAL_INSURANCE, "KNAPS-GI-", self.entry_date)

	def before_validate(self) -> None:
		set_nominee_minor_status(self)
		if self.has_multiple_members:
			set_insurance_member_date_of_birth(self)

	def before_save(self) -> None:
		if self.has_multiple_members:
			set_primary_client(self)
		elif self.primary_client:
			self.client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.primary_client, "client_name")
		self._set_maturity_date_general()
		self._set_title()

	def validate(self) -> None:
		validate_premium_positive(self)
		validate_entry_date_not_future(self)
		self._validate_period()
		validate_start_date_before_maturity(self)
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_unique_nominees(self)
		if self.has_multiple_members:
			self._validate_holders()
			validate_member_minor_restrictions(self)
		if not self.is_existing_policy:
			validate_payments_required(self)
		validate_status_requirements(self)
		warn_missing_nominees(self)

	def _set_title(self) -> None:
		if self.client_name and self.policy_type:
			self.title = f"{self.client_name} - {self.policy_type}"
		elif self.client_name:
			self.title = self.client_name

	def _set_maturity_date_general(self) -> None:
		if not self.start_date:
			return
		start = getdate(self.start_date)
		if self.period_type == "Days":
			self.maturity_date = add_days(start, self.period)
		elif self.period_type == "Months":
			self.maturity_date = add_months(start, self.period)
		elif self.period_type == "Years":
			self.maturity_date = add_years(start, self.period)

	def _validate_period(self) -> None:
		if not self.period_type:
			frappe.throw(
				_("Period Type is required."),
				title=_("Invalid Period"),
			)
		if not self.period or self.period <= 0:
			frappe.throw(
				_("Period must be positive."),
				title=_("Invalid Period"),
			)

	def _validate_holders(self) -> None:
		holders = self.get("holders") or []
		if not holders:
			frappe.throw(
				_("At least one member is required."),
				title=_("Members Required"),
			)

		seen_holders: set[str] = set()
		primary_count = 0
		for h in holders:
			if not h.holder:
				continue
			if h.holder in seen_holders:
				display = frappe.db.get_value(DOCTYPE_CLIENT, h.holder, "client_name") or h.holder
				frappe.throw(
					_("{} appears more than once in the members table.").format(display),
					title=_("Duplicate Member"),
				)
			seen_holders.add(h.holder)
			if h.is_primary:
				primary_count += 1

		if primary_count == 0:
			frappe.throw(
				_("One member must be marked as primary."),
				title=_("Primary Member Required"),
			)
		if primary_count > 1:
			frappe.throw(
				_("Only one member can be marked as primary."),
				title=_("Invalid Primary"),
			)
