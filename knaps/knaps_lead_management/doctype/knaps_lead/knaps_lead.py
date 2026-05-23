# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KNAPSLead(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps_lead_management.doctype.knaps_lead_interest.knaps_lead_interest import (
			KNAPSLeadInterest,
		)

		email: DF.Data | None
		internal_notes: DF.TextEditor | None
		lead: DF.DynamicLink
		lead_interested_in: DF.TableMultiSelect[KNAPSLeadInterest]
		lead_name: DF.Data | None
		lead_type: DF.Link
		phone: DF.Phone | None
		preferred_contact_mode: DF.Literal["", "Phone", "Whatsapp", "Email"] | None
		primary_contact: DF.Link | None
		source: DF.Link
		status: DF.Literal["", "New", "Qualified", "Nurture", "Prospect", "Won", "Lost", "Junk"]
		utm_campaign: DF.Data | None
		utm_content: DF.Data | None
		utm_medium: DF.Data | None
		utm_source: DF.Data | None
		utm_term: DF.Data | None
		whatsapp: DF.Phone | None
	# end: auto-generated types

	def before_save(self):
		self._sync_lead_data()

	def _sync_lead_data(self):
		if not self.lead or not self.lead_type:
			return

		if self.lead_type == "KNAPS Individual":
			individual = frappe.get_cached_doc("KNAPS Individual", self.lead)
			self.lead_name = individual.full_name
			self.preferred_contact_mode = individual.preferred_contact_mode
			self.phone = individual.primary_phone
			self.whatsapp = individual.primary_whatsapp
			self.email = individual.primary_email
			self.primary_contact = None

		elif self.lead_type == "KNAPS Non Individual":
			entity = frappe.get_cached_doc("KNAPS Non Individual", self.lead)
			self.lead_name = entity.legal_name
			self.primary_contact = entity.primary_contact
			self.preferred_contact_mode = entity.preferred_contact_mode
			self.phone = entity.primary_contact_phone
			self.whatsapp = entity.primary_contact_whatsapp
			self.email = entity.primary_contact_email
