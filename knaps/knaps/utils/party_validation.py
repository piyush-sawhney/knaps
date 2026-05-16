# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def normalize_pan(doc):
	if doc.pan:
		doc.pan = doc.pan.upper().strip()


def validate_unique_pan(doc, doctype, label):
	if doc.pan:
		existing = frappe.db.exists(doctype, {"pan": doc.pan, "name": ["!=", doc.name]})
		if existing:
			frappe.throw(
				_("PAN {} is already linked to another {}").format(doc.pan, label),
				title=_("Duplicate PAN"),
			)


def validate_phone_primary(doc, check_whatsapp=False):
	if doc.phone_numbers and len(doc.phone_numbers) > 0:
		primary_phones = [p for p in doc.phone_numbers if p.is_primary]
		if len(primary_phones) == 0:
			frappe.throw(_("At least one phone must be marked as Primary"), title=_("Validation Error"))
		if len(primary_phones) > 1:
			frappe.throw(_("Only one phone can be marked as Primary"), title=_("Validation Error"))
		if check_whatsapp:
			whatsapp_phones = [p for p in doc.phone_numbers if p.is_whatsapp]
			if len(whatsapp_phones) > 1:
				frappe.throw(_("Only one phone can be marked as WhatsApp"), title=_("Validation Error"))


def validate_email_primary(doc, field="email_address"):
	emails = getattr(doc, field, [])
	if emails and len(emails) > 0:
		primary_emails = [e for e in emails if e.is_primary]
		if len(primary_emails) == 0:
			frappe.throw(_("At least one email must be marked as Primary"), title=_("Validation Error"))
		if len(primary_emails) > 1:
			frappe.throw(_("Only one email can be marked as Primary"), title=_("Validation Error"))


def validate_inactive_cannot_be_primary(doc, email_field="email_address", check_whatsapp=False):
	for phone in doc.phone_numbers or []:
		if not phone.is_active:
			if phone.is_primary:
				frappe.throw(
					_("Row #{}: Phone {} is inactive — cannot be Primary").format(phone.idx, phone.number)
				)
			if check_whatsapp and phone.is_whatsapp:
				frappe.throw(
					_("Row #{}: Phone {} is inactive — cannot be WhatsApp").format(phone.idx, phone.number)
				)
	emails = getattr(doc, email_field, [])
	for email in emails:
		if not email.is_active and email.is_primary:
			frappe.throw(
				_("Row #{}: Email {} is inactive —` cannot be Primary").format(email.idx, email.email_address)
			)


def validate_unique_phone_numbers(doc):
	seen = set()
	for phone in doc.phone_numbers or []:
		num = (phone.number or "").strip()
		if num in seen:
			frappe.throw(_("Duplicate phone number: {}").format(num), title=_("Duplicate Entry"))
		seen.add(num)


def validate_unique_emails(doc, field="email_address"):
	seen = set()
	for email in getattr(doc, field, []) or []:
		addr = (email.email_address or "").strip().lower()
		if addr in seen:
			frappe.throw(_("Duplicate email address: {}").format(addr), title=_("Duplicate Entry"))
		seen.add(addr)
