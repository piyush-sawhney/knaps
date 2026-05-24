# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSHealthInsurance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from knaps.knaps.doctype.knaps_payment.knaps_payment import KNAPSPayment
		from knaps.knaps_client_management.doctype.knaps_nominee.knaps_nominee import KNAPSNominee
		from knaps.knaps_insurance.doctype.knaps_insurance_member.knaps_insurance_member import KNAPSInsuranceMember

		broker_details: DF.Link | None
		client_name: DF.Data | None
		currency: DF.Link | None
		entry_date: DF.Date
		holders: DF.Table[KNAPSInsuranceMember]
		holding_type: DF.Literal["Multi-Individual", "Floater"]
		insurance_plan_name: DF.Data | None
		investment_company: DF.Link
		is_existing_policy: DF.Check
		maturity_date: DF.Date | None
		nominees: DF.Table[KNAPSNominee]
		partner: DF.Link | None
		payments: DF.Table[KNAPSPayment]
		period_in_months: DF.Int
		policy_number: DF.Data | None
		premium: DF.Currency
		primary_client: DF.Link | None
		start_date: DF.Date | None
		status: DF.Literal["Proposal", "Active", "Renewed", "Surrendered", "Rejected"]
		sum_insured: DF.Currency
		through_broker: DF.Check
		through_partner: DF.Check
		through_us: DF.Check
		title: DF.Data | None
	# end: auto-generated types

	pass
