# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
class KNAPSLead(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from knaps.knaps_lead_management.doctype.knaps_lead_interest.knaps_lead_interest import KNAPSLeadInterest

		age: DF.Int
		email: DF.Data | None
		gender: DF.Link | None
		internal_notes: DF.TextEditor | None
		lead: DF.Link
		lead_interested_in: DF.TableMultiSelect[KNAPSLeadInterest]
		lead_name: DF.Data | None
		lead_type: DF.Literal["", "Individual", "Non-Individual"]
		organisation_name: DF.Link | None
		phone: DF.Phone | None
		preferred_contact_mode: DF.Data | None
		source: DF.Link
		status: DF.Literal["", "New", "Qualified", "Nurture", "Prospect", "Won", "Lost", "Junk"]
		utm_campaign: DF.Data | None
		utm_content: DF.Data | None
		utm_medium: DF.Data | None
		utm_source: DF.Data | None
		utm_term: DF.Data | None
		whatsapp: DF.Phone | None
	# end: auto-generated types

	def validate(self):
		self.validate_unique_lead_name()
		self.validate_lead_type_and_organisation()
	
	def validate_lead_type_and_organisation(self):
		if self.lead_type == "Individual" and self.organisation_name:
			frappe.throw(
				_("Organisation Name should be empty for Individual lead type."),
				title=_("Invalid Lead Type")
			)
		elif self.lead_type == "Non-Individual" and not self.organisation_name:
			frappe.throw(
				_("Organisation Name is required for Non-Individual lead type."),
				title=_("Invalid Lead Type")
			)	
	
	def validate_unique_lead_name(self):
		if self.lead_name:
			exists = frappe.db.exists(
				"KNAPS Lead",
				{
					"lead": self.lead,
					"status": ["not in", ["Lost", "Won", "Junk"]],
					"name": ["!=", self.name],
					"lead_type": self.lead_type
				}
			)

			if exists:
				frappe.throw(
					_(f"A lead with the name '{self.lead_name}' already exists."),
					title=_("Duplicate Lead Name")
				)