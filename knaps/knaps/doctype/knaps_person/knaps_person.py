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
from frappe.utils import getdate, today
from dateutil.relativedelta import relativedelta

class KNAPSPerson(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from knaps.knaps.doctype.knaps_email.knaps_email import KNAPSEmail
		from knaps.knaps.doctype.knaps_phone_number.knaps_phone_number import KNAPSPhoneNumber

		age: DF.Int
		date_of_birth: DF.Date | None
		display_picture: DF.AttachImage | None
		email_address: DF.Table[KNAPSEmail]
		first_name: DF.Data
		full_name: DF.Data | None
		gender: DF.Link
		last_name: DF.Data | None
		marital_status: DF.Literal["", "Single", "Married", "Widowed", "Divorced"]
		middle_name: DF.Data | None
		pan: DF.Data | None
		phone_numbers: DF.Table[KNAPSPhoneNumber]
		preferred_contact_mode: DF.Literal["", "Phone", "Whatsapp", "Email"]
		primary_email: DF.Data | None
		primary_household: DF.Link | None
		primary_phone: DF.Phone | None
		primary_whatsapp: DF.Phone | None
		salutation: DF.Link
		status: DF.Literal["Active", "Passive", "Deceased"]
	# end: auto-generated types
	def onload(self):
		load_address_and_contact(self)

	def on_trash(self):
		delete_contact_and_address("Member", self.name)

	
	def on_update(self):
		"""Update all linked Clients when Person is saved"""
		self.update_linked_clients()

	def update_linked_clients(self):
		"""Sync all linked Clients with latest Person data"""
		clients = frappe.get_all("KNAPS Client", filters={"person": self.name}, pluck="name")
		for client_name in clients:
			try:
				client = frappe.get_doc("KNAPS Client", client_name)
				client.run_method("sync_all_from_link")
				client.save(ignore_permissions=True)
			except Exception:
				frappe.logger().error(f"Error updating linked client {client_name}: {frappe.get_traceback()}")

	def validate(self):
		self.update_full_name()
		self.normalize_pan()
		self.validate_unique_pan()
		self.validate_pan_format()
		self.validate_preferred_contact_mode()
		self.sync_primary_fields_from_child_tables()
		self.validate_single_primary()
		self.validate_at_least_one_primary()
		self.validate_date_of_birth()
		self.validate_age()

	def validate_age(self):
		if self.date_of_birth:
			diff = relativedelta(
				getdate(today()),
				getdate(self.date_of_birth)
			)

			self.age_formatted = (
				f"{diff.years} Years "
				f"{diff.months} Months "
				f"{diff.days} Days"
			)

			self.age = diff.years

		else:
			self.age = None
			self.age_formatted = None

	def validate_preferred_contact_mode(self):
		if self.preferred_contact_mode:
			if self.preferred_contact_mode == "Phone" and not self.primary_phone:
				frappe.throw(_("Preferred contact mode is Phone but no primary phone number is set"), title=_("Validation Error"))
			elif self.preferred_contact_mode == "Whatsapp" and not self.primary_whatsapp:
				frappe.throw(_("Preferred contact mode is Whatsapp but no primary WhatsApp number is set"), title=_("Validation Error"))
			elif self.preferred_contact_mode == "Email" and not self.primary_email:
				frappe.throw(_("Preferred contact mode is Email but no primary email address is set"), title=_("Validation Error"))

	def update_full_name(self):
		"""Construct full name from first, middle, and last name"""
		# Trim whitespace from each component
		first = (self.first_name or "").strip()
		middle = (self.middle_name or "").strip()
		last = (self.last_name or "").strip()

		# Get old value for change detection (auditing)
		old_full_name = None
		if self.get_doc_before_save():
			old_full_name = self.get_doc_before_save().full_name

		# Construct full name with proper spacing
		parts = [first, middle, last]
		self.full_name = " ".join([part for part in parts if part])

		# Log when full name changes (for debugging/auditing)
		if old_full_name != self.full_name:
			frappe.logger().debug(
				f"Full name updated for {self.name or 'new record'}: '{old_full_name}' -> '{self.full_name}'"
			)

	def sync_primary_fields_from_child_tables(self):
		"""Extract primary values from child tables and sync to parent fields"""
		# Initialize with empty strings if not already set
		if not self.primary_phone:
			self.primary_phone = ""
		if not self.primary_whatsapp:
			self.primary_whatsapp = ""
		if not self.primary_email:
			self.primary_email = ""

		# Get primary phone
		for phone in self.phone_numbers or []:
			if phone.is_primary:
				self.primary_phone = phone.number or ""
				break

		# Get primary WhatsApp
		for phone in self.phone_numbers or []:
			if phone.is_whatsapp:
				self.primary_whatsapp = phone.number or ""
				break

		# Get primary email
		for email in self.email_address or []:
			if email.is_primary:
				self.primary_email = email.email_address or ""
				break

	def validate_single_primary(self):
		"""Ensure only one primary per category"""
		# Ensure only one primary phone
		primary_phones = [p for p in (self.phone_numbers or []) if p.is_primary]
		if len(primary_phones) > 1:
			frappe.throw(_("Only one phone can be marked as Primary"), title=_("Validation Error"))

		# Ensure only one WhatsApp
		whatsapp_phones = [p for p in (self.phone_numbers or []) if p.is_whatsapp]
		if len(whatsapp_phones) > 1:
			frappe.throw(_("Only one phone can be marked as WhatsApp"), title=_("Validation Error"))

		# Ensure only one primary email
		primary_emails = [e for e in (self.email_address or []) if e.is_primary]
		if len(primary_emails) > 1:
			frappe.throw(_("Only one email can be marked as Primary"), title=_("Validation Error"))

	def validate_at_least_one_primary(self):
		"""Ensure at least one primary exists if rows are present"""
		# Check phone numbers - if there are rows, at least one should be primary
		if self.phone_numbers and len(self.phone_numbers) > 0:
			has_primary = any(p.is_primary for p in self.phone_numbers)
			if not has_primary:
				frappe.throw(
					_("At least one phone number must be marked as Primary"), title=_("Validation Error")
				)

		# Check emails - if there are rows, at least one should be primary
		if self.email_address and len(self.email_address) > 0:
			has_primary = any(e.is_primary for e in self.email_address)
			if not has_primary:
				frappe.throw(_("At least one email must be marked as Primary"), title=_("Validation Error"))

	def normalize_pan(self):
		"""Normalize PAN to uppercase and stripped"""
		if self.pan:
			self.pan = self.pan.upper().strip()

	def validate_unique_pan(self):
		"""Ensure PAN is unique if provided"""
		if self.pan:
			# Check if PAN already exists (excluding current document)
			existing = frappe.db.exists("KNAPS Person", {"pan": self.pan, "name": ["!=", self.name]})
			if existing:
				frappe.throw(
					_("PAN {0} is already linked to another person").format(self.pan),
					title=_("Duplicate PAN"),
				)

	def validate_pan_format(self):
		"""Validate PAN format: 1-3 letters, 4th='P', 5th letter, 6-9 digits, 10th letter"""
		if self.pan and len(self.pan) == 10:
			# Check 4th character is 'P'
			if not self.pan[0:5].isalpha():
				frappe.throw(
					_("First 5 characters of PAN must be letters"),
					title=_("Invalid PAN Format")
				)

			# 4th character must be P
			if self.pan[3] != "P":
				frappe.throw(
					_("4th character of PAN must be 'P'"),
					title=_("Invalid PAN Format")
				)

			# Check 6-9 are digits
			if not self.pan[5:9].isdigit():
				frappe.throw(_("Characters 6-9 of PAN must be digits"), title=_("Invalid PAN Format"))

			# Check 10th is letter
			if not self.pan[9].isalpha():
				frappe.throw(_("10th character of PAN must be a letter"), title=_("Invalid PAN Format"))

	def validate_date_of_birth(self):
		if self.date_of_birth:
			if getdate(self.date_of_birth) > getdate(today()):
				frappe.throw(
					_("Date of Birth cannot be in the future"),
					title=_("Invalid Date")
				)