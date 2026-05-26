import frappe
from frappe import _
from frappe.model.document import Document


def normalize_pan(doc: Document) -> None:
	if doc.pan:
		doc.pan = doc.pan.upper().strip()


def validate_unique_pan(doc: Document, doctype: str, label: str) -> None:
	if doc.pan:
		existing = frappe.db.exists(doctype, {"pan": doc.pan, "name": ["!=", doc.name]})
		if existing:
			frappe.throw(
				_("PAN {} is already linked to another {}").format(doc.pan, label),
				title=_("Duplicate PAN"),
			)


def validate_phone_primary(doc: Document, check_whatsapp: bool = False) -> None:
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


def validate_email_primary(doc: Document, field: str = "email_address") -> None:
	emails = getattr(doc, field, [])
	if emails and len(emails) > 0:
		primary_emails = [e for e in emails if e.is_primary]
		if len(primary_emails) == 0:
			frappe.throw(_("At least one email must be marked as Primary"), title=_("Validation Error"))
		if len(primary_emails) > 1:
			frappe.throw(_("Only one email can be marked as Primary"), title=_("Validation Error"))


def validate_inactive_cannot_be_primary(
	doc: Document, email_field: str = "email_address", check_whatsapp: bool = False
) -> None:
	for phone in doc.phone_numbers or []:
		if not phone.is_active:
			if phone.is_primary:
				frappe.throw(
					_("Row #{}: Phone {} is inactive — cannot be Primary").format(phone.idx, phone.number),
					title=_("Inactive Contact"),
				)
			if check_whatsapp and phone.is_whatsapp:
				frappe.throw(
					_("Row #{}: Phone {} is inactive — cannot be WhatsApp").format(phone.idx, phone.number),
					title=_("Inactive Contact"),
				)
	emails = getattr(doc, email_field, [])
	for email in emails:
		if not email.is_active and email.is_primary:
			frappe.throw(
				_("Row #{}: Email {} is inactive — cannot be Primary").format(email.idx, email.email_address)
			)


def validate_unique_phone_numbers(doc: Document) -> None:
	seen = set()
	for phone in doc.phone_numbers or []:
		num = (phone.number or "").strip()
		if num in seen:
			frappe.throw(_("Duplicate phone number: {}").format(num), title=_("Duplicate Entry"))
		seen.add(num)


def validate_unique_emails(doc: Document, field: str = "email_address") -> None:
	seen = set()
	for email in getattr(doc, field, []) or []:
		addr = (email.email_address or "").strip().lower()
		if addr in seen:
			frappe.throw(_("Duplicate email address: {}").format(addr), title=_("Duplicate Entry"))
		seen.add(addr)
