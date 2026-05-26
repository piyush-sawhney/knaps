# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, getdate

from knaps.utils.shared import (
	build_nominee_name_cache,
	generate_investment_name,
	set_nominee_minor_status,
	validate_entry_date_not_future,
	validate_nominee_minor_guardian,
	validate_nominee_percent_total,
	validate_payments_required,
	validate_period_in_months,
	validate_unique_nominees,
)


class KNAPSVehicleInsurance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_payment.knaps_payment import KNAPSPayment
		from knaps.knaps_client_management.doctype.knaps_nominee.knaps_nominee import KNAPSNominee

		broker_details: DF.Link | None
		chassis_number: DF.Data | None
		client_name: DF.Data | None
		currency: DF.Link | None
		discount: DF.Float
		engine_number: DF.Data | None
		entry_date: DF.Date
		holding_type: DF.Literal["Private Car", "Two Wheeler", "Commercial"]
		idv: DF.Currency
		insurance_plan_name: DF.Data | None
		investment_company: DF.Link
		is_existing_policy: DF.Check
		maturity_date: DF.Date | None
		no_claim_bonus: DF.Float
		nominees: DF.Table[KNAPSNominee]
		partner: DF.Link | None
		payments: DF.Table[KNAPSPayment]
		period_in_months: DF.Int
		policy_document: DF.Attach | None
		policy_number: DF.Data | None
		premium: DF.Currency
		primary_client: DF.Link | None
		quote_number: DF.Data | None
		start_date: DF.Date | None
		status: DF.Literal["Proposal", "Active", "Renewed", "Surrendered", "Rejected"]
		through_broker: DF.Check
		through_partner: DF.Check
		through_us: DF.Check
		title: DF.Data | None
		tp_loading: DF.Float
		vehicle_make: DF.Data | None
		vehicle_model: DF.Data | None
		vehicle_number: DF.Data
	# end: auto-generated types

	def autoname(self) -> None:
		self.name = generate_investment_name("KNAPS Vehicle Insurance", "KNAPS-VIN-", self.entry_date)

	def before_validate(self) -> None:
		set_nominee_minor_status(self)

	def before_save(self) -> None:
		self._set_maturity_date()
		self._set_title()

	def validate(self) -> None:
		self._nominee_name_cache = build_nominee_name_cache(self)
		self._validate_premium_positive()
		validate_period_in_months(self)
		validate_entry_date_not_future(self)
		self._validate_start_date_before_maturity()
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_unique_nominees(self)
		if not self.is_existing_policy:
			validate_payments_required(self)
		self._validate_status_requirements()
		self._warn_missing_nominees()

	def _set_maturity_date(self) -> None:
		if self.start_date:
			self.maturity_date = add_months(getdate(self.start_date), self.period_in_months)

	def _set_title(self) -> None:
		if self.client_name and self.vehicle_number:
			self.title = f"{self.client_name} - {self.vehicle_number}"
		elif self.vehicle_number:
			self.title = self.vehicle_number
		elif self.client_name:
			self.title = self.client_name

	def _validate_premium_positive(self) -> None:
		if not self.premium or self.premium <= 0:
			frappe.throw(_("Premium must be positive."), title=_("Invalid Premium"))

	def _validate_start_date_before_maturity(self) -> None:
		if self.start_date and self.maturity_date:
			if getdate(self.start_date) >= getdate(self.maturity_date):
				frappe.throw(
					_("Start Date must be before Maturity Date."),
					title=_("Invalid Date Range"),
				)

	def _validate_status_requirements(self) -> None:
		if self.status in ("Proposal", "Rejected"):
			if self.policy_number:
				frappe.throw(
					_("Policy Number must be empty when status is {}.").format(self.status),
					title=_("Invalid Status"),
				)
			if self.policy_document:
				frappe.throw(
					_("Policy Document must be empty when status is {}.").format(self.status),
					title=_("Invalid Status"),
				)

		elif self.status in ("Active", "Renewed", "Surrendered"):
			if not self.start_date:
				frappe.throw(
					_("Start Date is required when status is {}.").format(self.status),
					title=_("Missing Start Date"),
				)
			if not self.policy_number:
				frappe.throw(
					_("Policy Number is required when status is {}.").format(self.status),
					title=_("Missing Policy Number"),
				)
			if not self.policy_document:
				frappe.throw(
					_("Policy Document is required when status is {}.").format(self.status),
					title=_("Missing Policy Document"),
				)

	def _warn_missing_nominees(self) -> None:
		if not self.get("nominees") and not self.is_existing_policy:
			frappe.msgprint(
				_("Consider adding nominees for this policy."),
				title=_("Nominees Recommended"),
				indicator="orange",
			)
