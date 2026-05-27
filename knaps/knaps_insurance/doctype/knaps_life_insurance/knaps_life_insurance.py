# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, add_years, getdate

from knaps.utils.constants import DOCTYPE_CLIENT, DOCTYPE_LIFE_INSURANCE
from knaps.utils.insurance import (
	validate_premium_positive,
	validate_start_date_before_maturity,
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


class KNAPSLifeInsurance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_payment.knaps_payment import KNAPSPayment
		from knaps.knaps_client_management.doctype.knaps_nominee.knaps_nominee import KNAPSNominee
		from knaps.knaps_insurance.doctype.knaps_life_insurance_member.knaps_life_insurance_member import (
			KNAPSLifeInsuranceMember,
		)
		from knaps.knaps_insurance.doctype.knaps_life_insurance_rider.knaps_life_insurance_rider import (
			KNAPSLifeInsuranceRider,
		)

		base_sum_assured: DF.Currency
		broker_details: DF.Link | None
		client_name: DF.Data | None
		currency: DF.Link | None
		entry_date: DF.Date
		has_multiple_members: DF.Check
		holders: DF.Table[KNAPSLifeInsuranceMember]
		insurance_plan_name: DF.Link
		insurer: DF.Link | None
		is_existing_policy: DF.Check
		maturity_date: DF.Date | None
		nominees: DF.Table[KNAPSNominee]
		notes: DF.TextEditor | None
		partner: DF.Link | None
		payments: DF.Table[KNAPSPayment]
		period: DF.Int
		period_type: DF.Literal["", "Days", "Months", "Years"]
		policy_document: DF.Attach | None
		policy_number: DF.Data | None
		policy_type: DF.Literal["", "Term", "Endowment", "Money Back", "ULIP", "Whole Life", "Pension Plan"]
		premium: DF.Currency
		premium_mode: DF.Literal["", "Single", "Monthly", "Quarterly", "Half-Yearly", "Yearly"]
		primary_client: DF.Link | None
		quote_number: DF.Data | None
		riders: DF.Table[KNAPSLifeInsuranceRider]
		start_date: DF.Date | None
		status: DF.Literal["Proposal", "Active", "Renewed", "Surrendered", "Rejected", "Lapsed"]
		through_broker: DF.Check
		through_partner: DF.Check
		through_us: DF.Check
		title: DF.Data | None
		total_premium: DF.Currency
	# end: auto-generated types

	def autoname(self) -> None:
		self.name = generate_investment_name(DOCTYPE_LIFE_INSURANCE, "KNAPS-LI-", self.entry_date)

	def before_validate(self) -> None:
		set_nominee_minor_status(self)

	def before_save(self) -> None:
		self._set_primary_client()
		self._set_maturity_date()
		self._set_title()
		self._compute_total_premium()

	def validate(self) -> None:
		self._nominee_name_cache = build_nominee_name_cache(self)
		self._validate_members()
		self._validate_member_minor_restrictions()
		validate_premium_positive(self)
		self._validate_period()
		validate_entry_date_not_future(self)
		validate_start_date_before_maturity(self)
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_unique_nominees(self)
		self._validate_nominee_not_member()
		if not self.is_existing_policy:
			validate_payments_required(self)
		self._validate_lapsed_status()
		validate_status_requirements(self)
		warn_missing_nominees(self)

	def _validate_lapsed_status(self) -> None:
		if self.status != "Lapsed":
			return
		if not self.start_date:
			frappe.throw(
				_("Start Date is required when status is Lapsed."),
				title=_("Missing Start Date"),
			)
		if not self.policy_number:
			frappe.throw(
				_("Policy Number is required when status is Lapsed."),
				title=_("Missing Policy Number"),
			)
		if not self.policy_document:
			frappe.throw(
				_("Policy Document is required when status is Lapsed."),
				title=_("Missing Policy Document"),
			)

	def _set_primary_client(self) -> None:
		members = self.get("holders") or []
		if not self.has_multiple_members or not members:
			if self.primary_client:
				self.client_name = frappe.db.get_value(DOCTYPE_CLIENT, self.primary_client, "client_name")
			return

		primary_members = [m for m in members if m.is_primary_member]
		if not primary_members:
			frappe.throw(
				_("One member must be marked as primary."),
				title=_("Primary Member Required"),
			)
		if len(primary_members) > 1:
			frappe.throw(
				_("Only one member can be marked as primary."),
				title=_("Invalid Primary"),
			)

		primary = primary_members[0]
		if primary.is_minor:
			display = frappe.db.get_value(DOCTYPE_CLIENT, primary.member, "client_name") or primary.member
			frappe.throw(
				_("{} is a minor and cannot be a primary member.").format(display),
				title=_("Minor Primary Member"),
			)

		self.primary_client = primary.member
		client_name = frappe.db.get_value(DOCTYPE_CLIENT, primary.member, "client_name")
		if client_name:
			self.client_name = client_name

	def _set_maturity_date(self) -> None:
		if not self.start_date:
			return
		start = getdate(self.start_date)
		if self.period_type == "Days":
			self.maturity_date = add_days(start, self.period)
		elif self.period_type == "Months":
			self.maturity_date = add_months(start, self.period)
		elif self.period_type == "Years":
			self.maturity_date = add_years(start, self.period)

	def _set_title(self) -> None:
		if self.client_name and self.policy_type:
			self.title = f"{self.client_name} - {self.policy_type}"
		elif self.client_name:
			self.title = self.client_name

	def _compute_total_premium(self) -> None:
		if not self.premium or not self.premium_mode or self.premium_mode == "Single":
			self.total_premium = self.premium
			return

		duration_months = self._get_duration_months()
		if duration_months <= 0:
			self.total_premium = self.premium
			return

		premium_periods = {
			"Monthly": 1,
			"Quarterly": 3,
			"Half-Yearly": 6,
			"Yearly": 12,
		}
		period_months = premium_periods.get(self.premium_mode, 1)
		num_payments = duration_months // period_months
		self.total_premium = self.premium * num_payments

	def _get_duration_months(self) -> int:
		if not self.period or self.period <= 0:
			return 0
		if self.period_type == "Months":
			return self.period
		if self.period_type == "Years":
			return self.period * 12
		return 0

	def _validate_members(self) -> None:
		members = self.get("holders") or []
		if not self.has_multiple_members:
			if members:
				frappe.throw(
					_("Members table should be empty when the policy does not have multiple members."),
					title=_("Unexpected Members"),
				)
			return

		if not members:
			frappe.throw(
				_("At least one member is required when the policy has multiple members."),
				title=_("Members Required"),
			)

		seen: set[tuple[str, str]] = set()
		proposer_members: set[str] = set()
		insured_members: set[str] = set()
		primary_count = 0

		for m in members:
			if not m.member:
				continue

			key = (m.member, m.role)
			if key in seen:
				display = frappe.db.get_value(DOCTYPE_CLIENT, m.member, "client_name") or m.member
				frappe.throw(
					_("{} appears more than once with the same role.").format(display),
					title=_("Duplicate Member"),
				)
			seen.add(key)

			if m.role == "Proposer":
				proposer_members.add(m.member)
			elif m.role == "Insured Member":
				insured_members.add(m.member)

			if m.is_primary_member:
				primary_count += 1

		if not proposer_members:
			frappe.throw(
				_("At least one member with role 'Proposer' is required."),
				title=_("Proposer Required"),
			)
		if not insured_members:
			frappe.throw(
				_("At least one member with role 'Insured Member' is required."),
				title=_("Insured Member Required"),
			)
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

	def _validate_member_minor_restrictions(self) -> None:
		members = self.get("holders") or []
		for m in members:
			if not m.is_minor:
				continue
			if m.role == "Proposer":
				display = frappe.db.get_value(DOCTYPE_CLIENT, m.member, "client_name") or m.member
				frappe.throw(
					_("{} is a minor and cannot be a Proposer.").format(display),
					title=_("Invalid Member Role"),
				)
			if m.is_primary_member:
				display = frappe.db.get_value(DOCTYPE_CLIENT, m.member, "client_name") or m.member
				frappe.throw(
					_("{} is a minor and cannot be a primary member.").format(display),
					title=_("Minor Primary Member"),
				)

		non_minor_members = [m for m in members if not m.is_minor]
		if members and not non_minor_members:
			frappe.throw(
				_("At least one member must not be a minor."),
				title=_("Minor Members Only"),
			)

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

	def _validate_nominee_not_member(self) -> None:
		members = self.get("holders") or []
		nominees = self.get("nominees") or []
		if not members or not nominees:
			return

		member_names = [m.member for m in members if m.member]
		if not member_names:
			return

		client_data = frappe.db.get_all(
			DOCTYPE_CLIENT,
			filters={"name": ["in", member_names]},
			fields=["name", "individual"],
		)
		member_individuals: set[str] = {c["individual"] for c in client_data if c.get("individual")}
		if not member_individuals:
			return

		for n in nominees:
			if n.nominee_name in member_individuals:
				display = self._nominee_name_cache.get(n.nominee_name, n.nominee_name)
				frappe.throw(
					_("Nominee {} cannot be a member of this policy.").format(display),
					title=_("Invalid Nominee"),
				)
