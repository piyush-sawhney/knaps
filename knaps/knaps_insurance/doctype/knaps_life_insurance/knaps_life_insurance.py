# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSLifeInsurance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_payment.knaps_payment import KNAPSPayment
		from knaps.knaps_client_management.doctype.knaps_nominee.knaps_nominee import KNAPSNominee
		from knaps.knaps_insurance.doctype.knaps_life_insurance_rider.knaps_life_insurance_rider import (
			KNAPSLifeInsuranceRider,
		)
		from knaps.knaps_life_insurance.doctype.knaps_life_insurance_member.knaps_life_insurance_member import (
			KNAPSLifeInsuranceMember,
		)

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
		policy_type: DF.Link
		premium: DF.Currency
		premium_mode: DF.Literal["", "Single", "Monthly", "Quarterly", "Half-Yearly", "Yearly"]
		primary_client: DF.Link | None
		quote_number: DF.Data | None
		riders: DF.Table[KNAPSLifeInsuranceRider]
		start_date: DF.Date | None
		status: DF.Literal["Proposal", "Active", "Renewed", "Surrendered", "Rejected", "Lapsed"]
		sum_assured: DF.Currency
		through_broker: DF.Check
		through_partner: DF.Check
		through_us: DF.Check
		title: DF.Data | None
		total_premium: DF.Currency
	# end: auto-generated types

	pass
