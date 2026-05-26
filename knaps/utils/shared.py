from datetime import date

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from knaps.utils.constants import DOCTYPE_INDIVIDUAL


def generate_investment_name(doctype: str, prefix_key: str, entry_date: date | str | None = None) -> str:
	entry_date = entry_date or date.today()
	if isinstance(entry_date, str):
		entry_date = getdate(entry_date)

	if entry_date.month >= 4:
		ty_start = entry_date.year
		ty_end = entry_date.year + 1
	else:
		ty_start = entry_date.year - 1
		ty_end = entry_date.year

	prefix = f"{prefix_key}{ty_start % 100:02d}-{ty_end % 100:02d}-"

	last_serial = 0
	last = frappe.db.get_value(
		doctype,
		{"name": ["like", f"{prefix}%"]},
		"name",
		order_by="name desc",
	)
	if last:
		last_serial = int(last.split("-")[-1])

	return f"{prefix}{last_serial + 1:08d}"


def set_nominee_minor_status(doc: Document) -> None:
	reference_date = doc.entry_date or today()
	for nominee in doc.get("nominees") or []:
		if nominee.nominee_date_of_birth:
			age = relativedelta(getdate(reference_date), getdate(nominee.nominee_date_of_birth)).years
			nominee.is_minor = 1 if age < 18 else 0


def build_nominee_name_cache(doc: Document) -> dict[str, str]:
	nominees = doc.get("nominees") or []
	if not nominees:
		return {}
	names = [n.nominee_name for n in nominees if n.nominee_name]
	if not names:
		return {}
	records = frappe.db.get_all(
		DOCTYPE_INDIVIDUAL,
		filters={"name": ["in", names]},
		fields=["name", "full_name"],
	)
	return {r["name"]: r["full_name"] or r["name"] for r in records}


def get_nominee_display(doc: Document, nominee) -> str:
	if not nominee.nominee_name:
		return ""
	cache: dict = getattr(doc, "_nominee_name_cache", {})
	return cache.get(nominee.nominee_name, nominee.nominee_name)


def validate_nominee_not_holder(doc: Document) -> None:
	holders = doc.get("holders") or []
	nominees = doc.get("nominees") or []
	if not holders or not nominees:
		return

	holder_names = [h.holder for h in holders]
	client_data = frappe.db.get_all(
		"KNAPS Client",
		filters={"name": ["in", holder_names]},
		fields=["name", "individual"],
	)
	holder_individuals: set[str] = {c["individual"] for c in client_data if c.get("individual")}

	for n in nominees:
		if n.nominee_name in holder_individuals:
			frappe.throw(
				_("Nominee {} cannot be a holder of this policy.").format(get_nominee_display(doc, n)),
				title=_("Invalid Nominee"),
			)


def validate_unique_nominees(doc: Document) -> None:
	seen: set[str] = set()
	for n in doc.get("nominees") or []:
		if n.nominee_name in seen:
			frappe.throw(
				_("Nominee {} appears more than once.").format(get_nominee_display(doc, n)),
				title=_("Duplicate Nominee"),
			)
		seen.add(n.nominee_name)


def validate_nominee_percent_total(doc: Document) -> None:
	nominees = doc.get("nominees") or []
	if not nominees:
		return
	total = 0.0
	for n in nominees:
		if not n.nominee_percent or n.nominee_percent <= 0:
			frappe.throw(
				_("Nominee {} must have a positive percentage.").format(get_nominee_display(doc, n)),
				title=_("Invalid Nominee Percent"),
			)
		total += n.nominee_percent
	if abs(total - 100.0) > 0.01:
		frappe.throw(
			_("Total nominee percentage must be 100. Currently it is {}.").format(total),
			title=_("Invalid Nominee Percent"),
		)


def validate_nominee_minor_guardian(doc: Document) -> None:
	for n in doc.get("nominees") or []:
		if n.is_minor and not n.guardian:
			frappe.throw(
				_("Guardian is required for minor nominee {}.").format(get_nominee_display(doc, n)),
				title=_("Guardian Required"),
			)


def validate_payments_required(doc: Document) -> None:
	if not doc.get("payments"):
		frappe.throw(
			_("At least one payment is required."),
			title=_("Payments Required"),
		)


def validate_entry_date_not_future(doc: Document) -> None:
	if getdate(doc.entry_date) > getdate(today()):
		frappe.throw(
			_("Entry Date cannot be in the future."),
			title=_("Invalid Entry Date"),
		)


def validate_period_in_months(doc: Document) -> None:
	if not doc.period_in_months or doc.period_in_months <= 0:
		frappe.throw(
			_("Period in months must be positive."),
			title=_("Invalid Period"),
		)
