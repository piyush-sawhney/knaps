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

from knaps.knaps.utils.party_validation import (
	normalize_pan,
	validate_email_primary,
	validate_inactive_cannot_be_primary,
	validate_phone_primary,
	validate_unique_emails,
	validate_unique_pan,
	validate_unique_phone_numbers,
)
from knaps.utils.constants import DOCTYPE_INDIVIDUAL
from knaps.utils.shared import calculate_age


class KNAPSIndividual(Document):
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
		family: DF.Link | None
		family_name: DF.Data | None
		first_name: DF.Data
		full_name: DF.Data | None
		gender: DF.Link
		last_name: DF.Data | None
		middle_name: DF.Data | None
		pan: DF.Data | None
		phone_numbers: DF.Table[KNAPSPhoneNumber]
		preferred_contact_mode: DF.Literal["", "Phone", "Whatsapp", "Email"]
		primary_email: DF.Data | None
		primary_phone: DF.Phone | None
		primary_whatsapp: DF.Phone | None
		profile_link: DF.Link | None
		salutation: DF.Link
		status: DF.Literal["Active", "Passive", "Deceased"]
	# end: auto-generated types

	def onload(self):
		load_address_and_contact(self)

	def on_trash(self):
		delete_contact_and_address(self.doctype, self.name)

	def validate(self):
		self.full_name = None
		self._update_full_name()
		normalize_pan(self)
		validate_unique_pan(self, DOCTYPE_INDIVIDUAL, "individual")
		self._validate_pan_format()
		validate_phone_primary(self, check_whatsapp=True)
		validate_email_primary(self, "email_address")
		validate_inactive_cannot_be_primary(self, "email_address", check_whatsapp=True)
		validate_unique_phone_numbers(self)
		validate_unique_emails(self, "email_address")
		self._sync_primary_fields_from_child_tables()
		self._validate_preferred_contact_mode()
		self._validate_date_of_birth()
		if self.date_of_birth:
			self.age = calculate_age(self.date_of_birth)

	@property
	def age_formatted(self):
		if not self.date_of_birth:
			return None
		diff = relativedelta(getdate(today()), getdate(self.date_of_birth))
		if diff.years == 0 and diff.months == 0 and diff.days == 0:
			return "Newborn"
		parts = []
		if diff.years:
			parts.append(f"{diff.years} Years")
		if diff.months:
			parts.append(f"{diff.months} Months")
		if diff.days:
			parts.append(f"{diff.days} Days")
		return " ".join(parts)

	def _validate_preferred_contact_mode(self) -> None:
		if not self.preferred_contact_mode:
			return

		mode_map = {
			"Phone": (self.phone_numbers or [], "is_primary"),
			"Whatsapp": (self.phone_numbers or [], "is_whatsapp"),
			"Email": (self.email_address or [], "is_primary"),
		}
		if self.preferred_contact_mode not in mode_map:
			return
		items, flag_attr = mode_map[self.preferred_contact_mode]
		self._assert_primary_exists(items, flag_attr)

	def _assert_primary_exists(self, items: list, flag_attr: str) -> None:
		primary = next((item for item in items if getattr(item, flag_attr)), None)
		if not primary:
			frappe.throw(
				_("A primary {} is required for {} mode.").format(flag_attr, self.preferred_contact_mode),
				title=_("Invalid Contact Mode"),
			)
		if not primary.is_active:
			frappe.throw(
				_("Primary {} is inactive. Activate it or choose another.").format(flag_attr),
				title=_("Invalid Contact Mode"),
			)

	def _update_full_name(self):
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

	def _sync_primary_fields_from_child_tables(self):
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

	def _validate_pan_format(self):
		"""Validate PAN format: 3 letters, 'P', 1 letter, 4 digits, 1 letter"""
		if self.pan:
			if len(self.pan) != 10:
				frappe.throw(_("PAN must be exactly 10 characters"), title=_("Invalid PAN Format"))
			if not PAN_REGEX.match(self.pan):
				frappe.throw(
					_("Invalid PAN format. Expected format: ABCPA1234D"), title=_("Invalid PAN Format")
				)

	def _validate_date_of_birth(self):
		if self.date_of_birth:
			if getdate(self.date_of_birth) > getdate(today()):
				frappe.throw(_("Date of Birth cannot be in the future"), title=_("Invalid Date"))
