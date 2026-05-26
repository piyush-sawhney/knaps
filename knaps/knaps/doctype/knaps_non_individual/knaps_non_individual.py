# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)
from frappe.model.document import Document

from knaps.knaps.utils.party_validation import (
	normalize_pan,
	validate_email_primary,
	validate_inactive_cannot_be_primary,
	validate_phone_primary,
	validate_unique_emails,
	validate_unique_pan,
	validate_unique_phone_numbers,
)
from knaps.utils.constants import DOCTYPE_INDIVIDUAL, DOCTYPE_NON_INDIVIDUAL

PAN_REGEX = re.compile(r"^[A-Z]{3}(.)[A-Z][0-9]{4}[A-Z]$")

TYPE_4TH_CHAR = {
	"Body of Individuals": "B",
	"Association of Persons": "A",
	"Hindu Undivided Family": "H",
	"Company": "C",
	"Limited Liability Partnership": "E",
	"Partnership Firm": "F",
	"Trust": "T",
	"Government Agency": "G",
	"Local Authority": "L",
	"Artificial Judicial Person": "J",
}


class KNAPSNonIndividual(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_email.knaps_email import KNAPSEmail
		from knaps.knaps.doctype.knaps_entity_contact.knaps_entity_contact import KNAPSEntityContact
		from knaps.knaps.doctype.knaps_phone_number.knaps_phone_number import KNAPSPhoneNumber

		contacts: DF.Table[KNAPSEntityContact]
		email_addresses: DF.Table[KNAPSEmail]
		entity_profile: DF.Link | None
		family: DF.Link | None
		family_name: DF.Data | None
		legal_name: DF.Data
		non_individual_type: DF.Link
		pan: DF.Data | None
		phone_numbers: DF.Table[KNAPSPhoneNumber]
		preferred_contact_mode: DF.Literal["", "Phone", "Whatsapp", "Email"] | None
		primary_contact: DF.Link | None
		primary_contact_email: DF.Data | None
		primary_contact_name: DF.Data | None
		primary_contact_phone: DF.Phone | None
		primary_contact_whatsapp: DF.Phone | None
		status: DF.Literal["Active", "Inactive"]
	# end: auto-generated types

	def onload(self):
		load_address_and_contact(self)

	def on_trash(self):
		delete_contact_and_address(self.doctype, self.name)

	def validate(self):
		self._normalize_legal_name()
		normalize_pan(self)
		self._validate_pan_format()
		validate_unique_pan(self, DOCTYPE_NON_INDIVIDUAL, "entity")
		self._sync_primary_contact()
		validate_phone_primary(self)
		validate_email_primary(self, "email_addresses")
		validate_inactive_cannot_be_primary(self, "email_addresses")
		validate_unique_phone_numbers(self)
		validate_unique_emails(self, "email_addresses")

	def _sync_primary_contact(self) -> None:
		primary = self._find_primary_contact()
		if not primary:
			primary = self._auto_promote_sole_contact()
		if primary:
			self._populate_from_individual(primary)
		else:
			self._clear_primary_fields()

	def _find_primary_contact(self) -> str | None:
		primary = None
		for row in self.contacts or []:
			if row.is_primary_contact:
				if primary:
					frappe.throw(
						_("Only one contact can be marked as primary."),
						title=_("Duplicate Primary Contact"),
					)
				primary = row.individual
		return primary

	def _auto_promote_sole_contact(self) -> str | None:
		if len(self.contacts or []) == 1:
			self.contacts[0].is_primary_contact = 1
			return self.contacts[0].individual
		return None

	def _populate_from_individual(self, individual_name: str) -> None:
		individual = frappe.get_cached_doc(DOCTYPE_INDIVIDUAL, individual_name)

		if individual.status == "Deceased":
			frappe.throw(
				_("Cannot set a deceased individual as primary contact."),
				title=_("Invalid Contact"),
			)

		self.primary_contact = individual_name
		self.primary_contact_name = individual.full_name or individual_name
		self.primary_contact_phone = individual.primary_phone or None
		self.primary_contact_whatsapp = individual.primary_whatsapp or None
		self.primary_contact_email = individual.primary_email or None
		self.preferred_contact_mode = individual.preferred_contact_mode or None

	def _clear_primary_fields(self) -> None:
		self.primary_contact = None
		self.primary_contact_name = None
		self.primary_contact_phone = None
		self.primary_contact_whatsapp = None
		self.primary_contact_email = None
		self.preferred_contact_mode = None

	def _normalize_legal_name(self):
		if self.legal_name:
			self.legal_name = " ".join(self.legal_name.split())

	def _validate_pan_format(self):
		if not self.pan:
			return
		if len(self.pan) != 10:
			frappe.throw(_("PAN must be exactly 10 characters"), title=_("Invalid PAN Format"))
		match = PAN_REGEX.match(self.pan)
		if not match:
			frappe.throw(_("Invalid PAN format. Expected format: ABCDA1234E"), title=_("Invalid PAN Format"))
		expected_4th = TYPE_4TH_CHAR.get(self.non_individual_type)
		if expected_4th and match.group(1) != expected_4th:
			frappe.throw(
				_("4th character of PAN must be '{}' for {}").format(expected_4th, self.non_individual_type),
				title=_("Invalid PAN Format"),
			)
