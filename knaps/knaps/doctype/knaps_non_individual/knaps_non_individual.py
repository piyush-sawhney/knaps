# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)

class KNAPSNonIndividual(Document):
	def onload(self):
		load_address_and_contact(self)
	
	def on_trash(self):
		delete_contact_and_address("Member", self.name)
		
	def validate(self):
		self.normalize_pan()
		self.validate_pan_format()
		self.validate_unique_pan()
		self.validate_date_of_incorporation()
		self.sync_primary_contact_from_signatories()
		self.validate_signatories_primary()
		self.validate_phone_primary()
		self.validate_email_primary()

	def normalize_pan(self):
		"""Normalize PAN to uppercase and strip whitespace"""
		if self.pan:
			self.pan = self.pan.upper().strip()

	def validate_pan_format(self):
		"""Validate PAN format for non-individual entities"""
		if self.pan:
			if len(self.pan) != 10:
				frappe.throw(
					_("PAN must be exactly 10 characters"),
					title=_("Invalid PAN Format")
				)

			# Mapping of non_individual_type to 4th character
			type_mapping = {
				"Body of Individuals": "B",
				"Association of Persons": "A",
				"Hindu Undivided Family": "H",
				"Company": "C",
				"Limited Liability Partnership": "E",
				"Partnership Firm": "F",
				"Trust": "T",
				"Government Agency": "G",
				"Local Authority": "L",
				"Artificial Judicial Person": "J"
			}

			# Check 4th character matches entity type
			expected_4th = type_mapping.get(self.non_individual_type)
			if expected_4th and self.pan[3] != expected_4th:
				frappe.throw(
					_("4th character of PAN must be '{0}' for {1}").format(
						expected_4th, self.non_individual_type
					),
					title=_("Invalid PAN Format")
				)

			# Validate positions 1-3 are letters
			if not self.pan[0:3].isalpha():
				frappe.throw(
					_("First 3 characters of PAN must be letters"),
					title=_("Invalid PAN Format")
				)

			# Validate position 5 is letter
			if not self.pan[4].isalpha():
				frappe.throw(
					_("5th character of PAN must be a letter"),
					title=_("Invalid PAN Format")
				)

			# Validate positions 6-9 are digits
			if not self.pan[5:9].isdigit():
				frappe.throw(
					_("Characters 6-9 of PAN must be digits"),
					title=_("Invalid PAN Format")
				)

			# Validate position 10 is letter
			if not self.pan[9].isalpha():
				frappe.throw(
					_("10th character of PAN must be a letter"),
					title=_("Invalid PAN Format")
				)

	def validate_unique_pan(self):
		"""Ensure PAN is unique if provided"""
		if self.pan:
			existing = frappe.db.exists(
				"KNAPS Non Individual",
				{
					"pan": self.pan,
					"name": ["!=", self.name]
				}
			)
			if existing:
				frappe.throw(
					_("PAN {0} is already linked to another entity").format(self.pan),
					title=_("Duplicate PAN")
				)

	def validate_date_of_incorporation(self):
		"""Ensure date of incorporation is not in the future"""
		if self.date_of_incoporation:
			if self.date_of_incoporation > frappe.utils.today():
				frappe.throw(
					_("Date of Incorporation cannot be in the future"),
					title=_("Invalid Date")
				)

	def sync_primary_contact_from_signatories(self):
		"""Sync primary contact from signatories table"""
		primary_signatory = None
		for signatory in (self.signatories or []):
			if signatory.is_primary_contact:
				primary_signatory = signatory
				break

		if primary_signatory and primary_signatory.signatory:
			self.primary_contact = primary_signatory.signatory
		else:
			self.primary_contact = ""
			self.primary_contact_phone = ""
			self.primary_contact_whatsapp = ""
			self.primary_contact_email = ""

	def validate_phone_primary(self):
		"""Validate phone numbers: at least one primary if rows exist, only one primary"""
		if self.phone_numbers and len(self.phone_numbers) > 0:
			primary_phones = [p for p in self.phone_numbers if p.is_primary]

			if len(primary_phones) == 0:
				frappe.throw(
					_("At least one phone must be marked as Primary"),
					title=_("Validation Error")
				)

			if len(primary_phones) > 1:
				frappe.throw(
					_("Only one phone can be marked as Primary"),
					title=_("Validation Error")
				)

	def validate_email_primary(self):
		"""Validate email addresses: at least one primary if rows exist, only one primary"""
		if self.email_addresses and len(self.email_addresses) > 0:
			primary_emails = [e for e in self.email_addresses if e.is_primary]

			if len(primary_emails) == 0:
				frappe.throw(
					_("At least one email must be marked as Primary"),
					title=_("Validation Error")
				)

			if len(primary_emails) > 1:
				frappe.throw(
					_("Only one email can be marked as Primary"),
					title=_("Validation Error")
				)

	def validate_signatories_primary(self):
		"""Validate signatories: at least one primary if rows exist, only one primary"""
		if self.signatories and len(self.signatories) > 0:
			primary_signatories = [s for s in self.signatories if s.is_primary_contact]

			if len(primary_signatories) == 0:
				frappe.throw(
					_("At least one signatory must be marked as Primary Contact"),
					title=_("Validation Error")
				)

			if len(primary_signatories) > 1:
				frappe.throw(
					_("Only one signatory can be marked as Primary Contact"),
					title=_("Validation Error")
				)