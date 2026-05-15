# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import re

PAN_REGEX = re.compile(r"^[A-Z]{3}P[A-Z][0-9]{4}[A-Z]$")

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)
from frappe.model.document import Document
from frappe.utils import getdate, today


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

	def validate(self):
		self.full_name = None
		self.update_full_name()
		self.normalize_pan()
		self.validate_unique_pan()
		self.validate_pan_format()
		self.validate_single_primary()
		self.validate_inactive_cannot_be_primary()
		self.validate_at_least_one_primary()
		self.validate_unique_phone_numbers()
		self.validate_unique_emails()
		self.sync_primary_fields_from_child_tables()
		self.validate_preferred_contact_mode()
		self.validate_date_of_birth()
		self.validate_age()

	def validate_age(self):
		if not self.has_value_changed("date_of_birth"):
			return
		if self.date_of_birth:
			diff = relativedelta(getdate(today()), getdate(self.date_of_birth))

			if diff.years == 0 and diff.months == 0 and diff.days == 0:
				self.age_formatted = "Newborn"
			elif diff.years == 0:
				self.age_formatted = f"{diff.months} Months {diff.days} Days"
			else:
				self.age_formatted = f"{diff.years} Years {diff.months} Months {diff.days} Days"

			self.age = diff.years
		else:
			self.age = None
			self.age_formatted = None

	def validate_preferred_contact_mode(self):
		if not self.preferred_contact_mode:
			return

		if self.preferred_contact_mode == "Phone":
			primary = next((p for p in (self.phone_numbers or []) if p.is_primary), None)
			if not primary:
				frappe.throw(_("Primary phone number is required for Phone mode"))
			if not primary.is_active:
				frappe.throw(_("Primary phone number is inactive. Activate it or choose another."))

		elif self.preferred_contact_mode == "Whatsapp":
			primary = next((p for p in (self.phone_numbers or []) if p.is_whatsapp), None)
			if not primary:
				frappe.throw(_("Primary WhatsApp number is required for WhatsApp mode"))
			if not primary.is_active:
				frappe.throw(_("Primary WhatsApp number is inactive. Activate it or choose another."))

		elif self.preferred_contact_mode == "Email":
			primary = next((e for e in (self.email_address or []) if e.is_primary), None)
			if not primary:
				frappe.throw(_("Primary email address is required for Email mode"))
			if not primary.is_active:
				frappe.throw(_("Primary email address is inactive. Activate it or choose another."))

	def update_full_name(self):
		"""Construct full name from first, middle, and last name"""
		# Trim whitespace from each component
		salutation = (self.salutation or "").strip()
		first = (self.first_name or "").strip()
		middle = (self.middle_name or "").strip()
		last = (self.last_name or "").strip()

		# Get old value for change detection (auditing)
		old_full_name = None
		if self.get_doc_before_save():
			old_full_name = self.get_doc_before_save().full_name

		# Construct full name with proper spacing
		parts = [salutation, first, middle, last]
		self.full_name = " ".join([part for part in parts if part])

		# Log when full name changes (for debugging/auditing)
		if old_full_name != self.full_name:
			frappe.logger().debug(
				f"Full name updated for {self.name or 'new record'}: '{old_full_name}' -> '{self.full_name}'"
			)

	def sync_primary_fields_from_child_tables(self):
		if not self.has_value_changed("phone_numbers") and not self.has_value_changed("email_address"):
			return

		self.primary_phone = ""
		self.primary_whatsapp = ""
		self.primary_email = ""

		for phone in self.phone_numbers or []:
			if phone.is_primary:
				self.primary_phone = phone.number or ""
				break

		for phone in self.phone_numbers or []:
			if phone.is_whatsapp:
				self.primary_whatsapp = phone.number or ""
				break

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
		"""Validate PAN format: 3 letters, 'P', 1 letter, 4 digits, 1 letter"""
		if self.pan and len(self.pan) == 10:
			if not PAN_REGEX.match(self.pan):
				frappe.throw(
					_("Invalid PAN format. Expected format: ABCPA1234D"), title=_("Invalid PAN Format")
				)

	def validate_date_of_birth(self):
		if self.date_of_birth:
			if getdate(self.date_of_birth) > getdate(today()):
				frappe.throw(_("Date of Birth cannot be in the future"), title=_("Invalid Date"))

	def validate_unique_phone_numbers(self):
		seen = set()
		for phone in self.phone_numbers or []:
			num = (phone.number or "").strip()
			if num in seen:
				frappe.throw(_("Duplicate phone number: {}").format(num), title=_("Duplicate Entry"))
			seen.add(num)

	def validate_unique_emails(self):
		seen = set()
		for email in self.email_address or []:
			addr = (email.email_address or "").strip().lower()
			if addr in seen:
				frappe.throw(_("Duplicate email address: {}").format(addr), title=_("Duplicate Entry"))
			seen.add(addr)

	def validate_inactive_cannot_be_primary(self):
		for phone in self.phone_numbers or []:
			if phone.is_active:
				continue
			if phone.is_primary:
				frappe.throw(
					_("Row #{}: Phone {} is inactive — cannot be Primary").format(phone.idx, phone.number)
				)
			if phone.is_whatsapp:
				frappe.throw(
					_("Row #{}: Phone {} is inactive — cannot be WhatsApp").format(phone.idx, phone.number)
				)
		for email in self.email_address or []:
			if not email.is_active and email.is_primary:
				frappe.throw(
					_("Row #{}: Email {} is inactive — cannot be Primary").format(
						email.idx, email.email_address
					)
				)
