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
		from knaps.knaps.doctype.knaps_phone_number.knaps_phone_number import KNAPSPhoneNumber

		email_addresses: DF.Table[KNAPSEmail]
		legal_name: DF.Data
		non_individual_type: DF.Link
		pan: DF.Data | None
		phone_numbers: DF.Table[KNAPSPhoneNumber]
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
		self.normalize_legal_name()
		self.normalize_pan()
		self.validate_pan_format()
		self.validate_unique_pan()
		self.validate_primary_contact()
		self.validate_phone_primary()
		self.validate_email_primary()
		self.validate_inactive_cannot_be_primary()
		self.validate_unique_phone_numbers()
		self.validate_unique_emails()

	def validate_inactive_cannot_be_primary(self):
		for phone in self.phone_numbers or []:
			if not phone.is_active and phone.is_primary:
				frappe.throw(_("Row #{}: Phone {} is inactive — cannot be Primary").format(phone.idx, phone.number))
		for email in self.email_addresses or []:
			if not email.is_active and email.is_primary:
				frappe.throw(_("Row #{}: Email {} is inactive — cannot be Primary").format(email.idx, email.email_address))
				
	def validate_primary_contact(self):
		if self.primary_contact:
			status = frappe.db.get_value("KNAPS Person", self.primary_contact, "status")
			if status == "Deceased":
				frappe.throw(_("Cannot set a deceased person as primary contact"), title=_("Invalid Contact"))

	def normalize_legal_name(self):
		if self.legal_name:
			self.legal_name = " ".join(self.legal_name.split())

	def normalize_pan(self):
		"""Normalize PAN to uppercase and strip whitespace"""
		if self.pan:
			self.pan = self.pan.upper().strip()

	def validate_pan_format(self):
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

	def validate_unique_pan(self):
		"""Ensure PAN is unique if provided"""
		if self.pan:
			existing = frappe.db.exists("KNAPS Non Individual", {"pan": self.pan, "name": ["!=", self.name]})
			if existing:
				frappe.throw(
					_("PAN {0} is already linked to another entity").format(self.pan),
					title=_("Duplicate PAN"),
				)

	def validate_unique_phone_numbers(self):
		seen = set()
		for phone in self.phone_numbers or []:
			num = (phone.number or "").strip()
			if num in seen:
				frappe.throw(_("Duplicate phone number: {}").format(num), title=_("Duplicate Entry"))
			seen.add(num)

	def validate_unique_emails(self):
		seen = set()
		for email in self.email_addresses or []:
			addr = (email.email_address or "").strip().lower()
			if addr in seen:
				frappe.throw(_("Duplicate email address: {}").format(addr), title=_("Duplicate Entry"))
			seen.add(addr)

	def validate_phone_primary(self):
		"""Validate phone numbers: at least one primary if rows exist, only one primary"""
		if self.phone_numbers and len(self.phone_numbers) > 0:
			primary_phones = [p for p in self.phone_numbers if p.is_primary]

			if len(primary_phones) == 0:
				frappe.throw(_("At least one phone must be marked as Primary"), title=_("Validation Error"))

			if len(primary_phones) > 1:
				frappe.throw(_("Only one phone can be marked as Primary"), title=_("Validation Error"))

	def validate_email_primary(self):
		"""Validate email addresses: at least one primary if rows exist, only one primary"""
		if self.email_addresses and len(self.email_addresses) > 0:
			primary_emails = [e for e in self.email_addresses if e.is_primary]

			if len(primary_emails) == 0:
				frappe.throw(_("At least one email must be marked as Primary"), title=_("Validation Error"))

			if len(primary_emails) > 1:
				frappe.throw(_("Only one email can be marked as Primary"), title=_("Validation Error"))
