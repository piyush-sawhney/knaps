# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KNAPSClient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		client_name: DF.Data | None
		client_pan: DF.Data | None
		client_type: DF.Literal["Individual", "Sole Proprietor", "Non Individual"]
		is_minor: DF.Check
		non_individual: DF.Link | None
		individual: DF.Link | None
		preferred_contact_mode: DF.Data | None
		primary_email: DF.Data | None
		primary_phone: DF.Phone | None
		primary_whatsapp: DF.Phone | None
		status: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self._sync_from_link()
		self._validate_required_links()
		self._validate_pan_uniqueness()

	def _sync_from_link(self):
		if self.client_type in ("Individual", "Sole Proprietor") and self.individual:
			individual = frappe.get_doc("KNAPS Individual", self.individual)
			self.client_pan = individual.pan or ""
			if self.client_type == "Individual":
				self.client_name = individual.full_name or ""
			self.primary_phone = individual.primary_phone or ""
			self.primary_whatsapp = individual.primary_whatsapp or ""
			self.primary_email = individual.primary_email or ""
			self.preferred_contact_mode = individual.preferred_contact_mode or ""
			self.status = individual.status or ""
			if self.client_type == "Individual":
				self.is_minor = 1 if individual.age and individual.age < 18 else 0

		elif self.client_type == "Non Individual" and self.non_individual:
			non_individual = frappe.get_doc("KNAPS Non Individual", self.non_individual)
			self.client_pan = non_individual.pan or ""
			self.client_name = non_individual.legal_name or ""
			self.status = non_individual.status or ""
			self.individual = non_individual.primary_contact or ""
			if self.individual:
				individual = frappe.get_doc("KNAPS Individual", self.individual)
				self.primary_phone = individual.primary_phone or ""
				self.primary_whatsapp = individual.primary_whatsapp or ""
				self.primary_email = individual.primary_email or ""
				self.preferred_contact_mode = individual.preferred_contact_mode or ""

	def _validate_required_links(self):
		if self.client_type in ("Individual", "Sole Proprietor") and not self.individual:
			frappe.throw(_("Individual is required for Individual or Sole Proprietor."), title=_("Validation Error"))
		if self.client_type == "Non Individual" and not self.non_individual:
			frappe.throw(_("Non Individual entity is required."), title=_("Validation Error"))

	def _validate_pan_uniqueness(self):
		if not self.client_pan:
			return
		filters = {"client_pan": self.client_pan, "name": ["!=", self.name]}
		if self.client_type == "Non Individual":
			filters["client_type"] = "Non Individual"
		elif self.client_type == "Individual":
			filters["client_type"] = "Individual"
		elif self.client_type == "Sole Proprietor":
			filters["client_type"] = "Sole Proprietor"
			filters["client_name"] = self.client_name
		if frappe.db.exists("KNAPS Client", filters):
			frappe.throw(_("Client with this PAN already exists."), title=_("Duplicate PAN"))
