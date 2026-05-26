# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from knaps.utils.insurance import (
	set_insurance_member_date_of_birth,
	set_maturity_date_general,
	validate_premium_positive,
	validate_status_requirements,
	warn_missing_nominees,
)
from knaps.utils.shared import (
	build_nominee_name_cache,
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
		self.name = generate_investment_name("KNAPS General Insurance", "KNAPS-GI-", self.entry_date)

	def before_validate(self) -> None:
		set_nominee_minor_status(self)
		if self.has_multiple_members:
			set_insurance_member_date_of_birth(self)

	def before_save(self) -> None:
		self._set_primary_client()
		set_maturity_date_general(self)
		self._set_title()

	def validate(self) -> None:
		self._nominee_name_cache = build_nominee_name_cache(self)
		validate_premium_positive(self)
		validate_entry_date_not_future(self)
		self._validate_period()
		self._validate_start_date_before_maturity()
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_unique_nominees(self)
		if self.has_multiple_members:
			self._validate_holders()
		if not self.is_existing_policy:
			validate_payments_required(self)
		validate_status_requirements(self)
		warn_missing_nominees(self)

	def _set_primary_client(self) -> None:
		if self.has_multiple_members:
			holders = self.get("holders") or []
			primary_holders = [h for h in holders if h.is_primary]
			if not primary_holders:
				self.primary_client = None
				self.client_name = None
				return
			if len(primary_holders) > 1:
				frappe.throw(
					_("Only one member can be marked as primary."),
					title=_("Invalid Primary"),
				)
			primary = primary_holders[0]
			self._validate_not_minor(primary)
			self.primary_client = primary.holder
		if self.primary_client:
			client_name = frappe.db.get_value("KNAPS Client", self.primary_client, "client_name")
			if client_name:
				self.client_name = client_name

	def _validate_not_minor(self, member) -> None:
		client = frappe.get_cached_doc("KNAPS Client", member.holder)
		if client.is_minor:
			display = frappe.db.get_value("KNAPS Client", member.holder, "client_name") or member.holder
			frappe.throw(
				_("{} is a minor and cannot be the primary member.").format(display),
				title=_("Minor Primary Member"),
			)

	def _set_title(self) -> None:
		if self.client_name and self.policy_type:
			self.title = f"{self.client_name} - {self.policy_type}"
		elif self.client_name:
			self.title = self.client_name

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

	def _validate_start_date_before_maturity(self) -> None:
		if self.start_date and self.maturity_date:
			if getdate(self.start_date) >= getdate(self.maturity_date):
				frappe.throw(
					_("Start Date must be before Maturity Date."),
					title=_("Invalid Date Range"),
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
				display = frappe.db.get_value("KNAPS Client", h.holder, "client_name") or h.holder
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
