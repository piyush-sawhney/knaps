# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from knaps.utils.insurance import (
	set_maturity_date,
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
		set_maturity_date(self)
		self._set_title()

	def validate(self) -> None:
		self._nominee_name_cache = build_nominee_name_cache(self)
		validate_premium_positive(self)
		validate_period_in_months(self)
		validate_entry_date_not_future(self)
		validate_start_date_before_maturity(self)
		validate_nominee_percent_total(self)
		validate_nominee_minor_guardian(self)
		validate_unique_nominees(self)
		if not self.is_existing_policy:
			validate_payments_required(self)
		validate_status_requirements(self)
		warn_missing_nominees(self)

	def _set_title(self) -> None:
		if self.client_name and self.vehicle_number:
			self.title = f"{self.client_name} - {self.vehicle_number}"
		elif self.vehicle_number:
			self.title = self.vehicle_number
		elif self.client_name:
			self.title = self.client_name
