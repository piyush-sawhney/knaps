# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)
from frappe.model.document import Document
from frappe import _

class KNAPSPerson(Document):
	def onload(self):
		load_address_and_contact(self)
	
	def on_trash(self):
		delete_contact_and_address("Member", self.name)
	
	def validate(self):
		self.update_full_name()
		self.normalize_pan()
		self.sync_primary_fields_from_child_tables()
		self.validate_single_primary()
		self.validate_at_least_one_primary()
		self.validate_unique_pan()
		self.validate_pan_format()
		self.validate_date_of_birth()
	
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
				f"Full name updated for {self.name or 'new record'}: "
				f"'{old_full_name}' -> '{self.full_name}'"
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
		for phone in (self.phone_numbers or []):
			if phone.is_primary:
				self.primary_phone = phone.number or ""
				break
		
		# Get primary WhatsApp
		for phone in (self.phone_numbers or []):
			if phone.is_whatsapp:
				self.primary_whatsapp = phone.number or ""
				break
		
		# Get primary email
		for email in (self.email_address or []):
			if email.is_primary:
				self.primary_email = email.email_address or ""
				break

	def validate_single_primary(self):
		"""Ensure only one primary per category"""
		# Ensure only one primary phone
		primary_phones = [p for p in (self.phone_numbers or []) if p.is_primary]
		if len(primary_phones) > 1:
			frappe.throw(
				_("Only one phone can be marked as Primary"),
				title=_("Validation Error")
			)
		
		# Ensure only one WhatsApp
		whatsapp_phones = [p for p in (self.phone_numbers or []) if p.is_whatsapp]
		if len(whatsapp_phones) > 1:
			frappe.throw(
				_("Only one phone can be marked as WhatsApp"),
				title=_("Validation Error")
			)
		
		# Ensure only one primary email
		primary_emails = [e for e in (self.email_address or []) if e.is_primary]
		if len(primary_emails) > 1:
			frappe.throw(
				_("Only one email can be marked as Primary"),
				title=_("Validation Error")
			)
	
	def validate_at_least_one_primary(self):
		"""Ensure at least one primary exists if rows are present"""
		# Check phone numbers - if there are rows, at least one should be primary
		if self.phone_numbers and len(self.phone_numbers) > 0:
			has_primary = any(p.is_primary for p in self.phone_numbers)
			if not has_primary:
				frappe.throw(
					_("At least one phone number must be marked as Primary"),
					title=_("Validation Error")
				)
		
		# Check emails - if there are rows, at least one should be primary
		if self.email_address and len(self.email_address) > 0:
			has_primary = any(e.is_primary for e in self.email_address)
			if not has_primary:
				frappe.throw(
					_("At least one email must be marked as Primary"),
					title=_("Validation Error")
				)
	
	def normalize_pan(self):
		"""Normalize PAN to uppercase and stripped"""
		if self.pan:
			self.pan = self.pan.upper().strip()
	
	def validate_unique_pan(self):
		"""Ensure PAN is unique if provided"""
		if self.pan:
			# Check if PAN already exists (excluding current document)
			existing = frappe.db.exists(
				"KNAPS Person",
				{
					"pan": self.pan,
					"name": ["!=", self.name]
				}
			)
			if existing:
				frappe.throw(
					_("PAN {0} is already linked to another person").format(self.pan),
					title=_("Duplicate PAN")
				)
	
	def validate_pan_format(self):
		"""Validate PAN format: 1-3 letters, 4th='P', 5th letter, 6-9 digits, 10th letter"""
		if self.pan and len(self.pan) == 10:
			# Check 4th character is 'P'
			if self.pan[3] != 'P':
				frappe.throw(
					_("4th character of PAN must be 'P'"),
					title=_("Invalid PAN Format")
				)
			
			# Check 1-3 are letters
			if not self.pan[0:3].isalpha():
				frappe.throw(
					_("First 3 characters of PAN must be letters"),
					title=_("Invalid PAN Format")
				)
			
			# Check 5th is letter
			if not self.pan[4].isalpha():
				frappe.throw(
					_("5th character of PAN must be a letter"),
					title=_("Invalid PAN Format")
				)
			
			# Check 6-9 are digits
			if not self.pan[5:9].isdigit():
				frappe.throw(
					_("Characters 6-9 of PAN must be digits"),
					title=_("Invalid PAN Format")
				)
			
			# Check 10th is letter
			if not self.pan[9].isalpha():
				frappe.throw(
					_("10th character of PAN must be a letter"),
					title=_("Invalid PAN Format")
				)
	
	def validate_date_of_birth(self):
		"""Ensure date of birth is not in the future"""
		if self.date_of_birth:
			if self.date_of_birth > frappe.utils.today():
				frappe.throw(
					_("Date of Birth cannot be in the future"),
					title=_("Invalid Date")
				)