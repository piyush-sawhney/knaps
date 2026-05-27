# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from knaps.utils.constants import DOCTYPE_CLIENT, DOCTYPE_INDIVIDUAL, DOCTYPE_NON_INDIVIDUAL


class KNAPSClient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		client_name: DF.Data | None
		client_type: DF.Literal["Individual", "Sole Proprietor", "Non Individual"]
		date_of_birth: DF.Date | None
		individual: DF.Link | None
		is_minor: DF.Check
		non_individual: DF.Link | None
		pan: DF.Data | None
		preferred_contact_mode: DF.Data | None
		primary_email: DF.Data | None
		primary_phone: DF.Phone | None
		primary_whatsapp: DF.Phone | None
		status: DF.Literal["Active", "Inactive", "Passive", "Deceased"]
	# end: auto-generated types

	def validate(self):
		self._validate_client_type_consistency()
		self._clear_incompatible_links()
		self._sync_from_linked_entity()
		self._sanitize_client_name()
		self._validate_pan_uniqueness()

	def _validate_client_type_consistency(self):
		if self.client_type in ("Individual", "Sole Proprietor") and not self.individual:
			frappe.throw(
				_("Individual is required for Client Type {}.").format(self.client_type),
				title=_("Missing Link"),
			)
		if self.client_type == "Non Individual" and not self.non_individual:
			frappe.throw(
				_("Non Individual is required for Client Type Non Individual."),
				title=_("Missing Link"),
			)

	def _sanitize_client_name(self):
		if self.client_name:
			self.client_name = " ".join(self.client_name.split())
		if not self.client_name and self.client_type == "Sole Proprietor":
			frappe.throw(
				_("Client Name is required for Sole Proprietor."),
				title=_("Missing Name"),
			)

	def _validate_pan_uniqueness(self):
		if not self.pan:
			return

		if self.client_type == "Non Individual":
			existing = frappe.db.exists(
				DOCTYPE_CLIENT,
				{"pan": self.pan, "client_type": "Non Individual", "name": ["!=", self.name]},
			)
			if existing:
				frappe.throw(
					_("PAN {} is already used by another Non Individual client.").format(self.pan),
					title=_("Duplicate PAN"),
				)

		elif self.client_type in ("Individual", "Sole Proprietor") and self.client_name:
			existing = frappe.db.exists(
				DOCTYPE_CLIENT,
				{
					"client_name": self.client_name,
					"pan": self.pan,
					"client_type": ["in", ["Individual", "Sole Proprietor"]],
					"name": ["!=", self.name],
				},
			)
			if existing:
				frappe.throw(
					_("A client with name '{}' and PAN '{}' already exists.").format(
						self.client_name, self.pan
					),
					title=_("Duplicate Client"),
				)

	def _clear_incompatible_links(self):
		if self.client_type in ("Individual", "Sole Proprietor"):
			if self.non_individual:
				self.non_individual = None
		elif self.client_type == "Non Individual":
			pass  # individual is used for primary contact person

	def _sync_from_linked_entity(self):
		if self.client_type in ("Individual", "Sole Proprietor") and self.individual:
			self._sync_from_individual()
		elif self.client_type == "Non Individual" and self.non_individual:
			self._sync_from_non_individual()

	def _sync_from_individual(self):
		individual = frappe.get_cached_doc(DOCTYPE_INDIVIDUAL, self.individual)

		if self.client_type == "Individual":
			self.client_name = individual.full_name
		# Sole Proprietor: client_name is manually entered, never overwritten

		self.pan = individual.pan
		self.status = individual.status
		self.primary_phone = individual.primary_phone
		self.primary_whatsapp = individual.primary_whatsapp
		self.primary_email = individual.primary_email
		self.preferred_contact_mode = individual.preferred_contact_mode
		self.date_of_birth = individual.date_of_birth
		if individual.date_of_birth:
			age = relativedelta(getdate(today()), getdate(individual.date_of_birth)).years
			self.is_minor = 1 if age < 18 else 0
		else:
			self.is_minor = 0

	def _sync_from_non_individual(self):
		entity = frappe.get_cached_doc(DOCTYPE_NON_INDIVIDUAL, self.non_individual)

		self.client_name = entity.legal_name
		self.pan = entity.pan
		self.status = entity.status
		self.date_of_birth = None
		self.is_minor = 0

		self.individual = entity.primary_contact
		self.primary_phone = entity.primary_contact_phone
		self.primary_whatsapp = entity.primary_contact_whatsapp
		self.primary_email = entity.primary_contact_email
		self.preferred_contact_mode = entity.preferred_contact_mode
