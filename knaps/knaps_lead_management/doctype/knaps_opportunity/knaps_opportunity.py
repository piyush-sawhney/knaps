# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document

from knaps.utils.constants import DOCTYPE_CLIENT, DOCTYPE_OPPORTUNITY


class KNAPSOpportunity(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps_lead_management.doctype.knaps_lead_interest.knaps_lead_interest import (
			KNAPSLeadInterest,
		)

		client: DF.Link
		client_name: DF.Data | None
		email: DF.Data | None
		internal_notes: DF.TextEditor | None
		opportunity_type: DF.TableMultiSelect[KNAPSLeadInterest]
		phone: DF.Phone | None
		source: DF.Link
		status: DF.Literal["New", "Qualified", "Nurture", "Prospect", "Won", "Lost", "Junk"]
		utm_campaign: DF.Data | None
		utm_content: DF.Data | None
		utm_medium: DF.Data | None
		utm_source: DF.Data | None
		utm_term: DF.Data | None
		whatsapp: DF.Phone | None
	# end: auto-generated types

	def before_save(self):
		self._sync_client_data()

	def _sync_client_data(self):
		if not self.client:
			return

		client = frappe.get_cached_doc(DOCTYPE_CLIENT, self.client)
		self.client_name = client.client_name
		self.phone = client.primary_phone
		self.whatsapp = client.primary_whatsapp
		self.email = client.primary_email

	def validate(self):
		self._validate_unique_opportunity()

	def _validate_unique_opportunity(self):
		if self.client:
			exists = frappe.db.exists(
				DOCTYPE_OPPORTUNITY,
				{
					"client": self.client,
					"status": ["not in", ["Lost", "Won", "Junk"]],
					"name": ["!=", self.name],
				},
			)

			if exists:
				frappe.throw(
					_("An opportunity already exists for client '{}'.").format(self.client_name),
					title=_("Duplicate Opportunity"),
				)
