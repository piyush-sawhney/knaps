from datetime import date

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from knaps.utils.constants import DOCTYPE_CLIENT, DOCTYPE_INDIVIDUAL


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


def calculate_age(date_of_birth: date | str, at_date: date | str | None = None) -> int:
	reference = getdate(at_date or today())
	return relativedelta(reference, getdate(date_of_birth)).years


def set_nominee_minor_status(doc: Document) -> None:
	reference_date = doc.entry_date or today()
	for nominee in doc.get("nominees") or []:
		if nominee.nominee_date_of_birth:
			nominee.is_minor = 1 if calculate_age(nominee.nominee_date_of_birth, reference_date) < 18 else 0


def get_nominee_display(nominee) -> str:
	if not nominee.nominee_name:
		return ""
	return nominee.nominee_name_capture or nominee.nominee_name


def validate_nominee_not_holder(doc: Document) -> None:
	holders = doc.get("holders") or []
	nominees = doc.get("nominees") or []
	if not holders or not nominees:
		return

	holder_names = [h.holder for h in holders]
	client_data = frappe.db.get_all(
		DOCTYPE_CLIENT,
		filters={"name": ["in", holder_names]},
		fields=["name", "individual"],
	)
	holder_individuals: set[str] = {c["individual"] for c in client_data if c.get("individual")}

	for n in nominees:
		if n.nominee_name in holder_individuals:
			frappe.throw(
				_("Nominee {} cannot be a holder of this policy.").format(get_nominee_display(n)),
				title=_("Invalid Nominee"),
			)


def validate_unique_nominees(doc: Document) -> None:
	seen: set[str] = set()
	for n in doc.get("nominees") or []:
		if n.nominee_name in seen:
			frappe.throw(
				_("Nominee {} appears more than once.").format(get_nominee_display(n)),
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
				_("Nominee {} must have a positive percentage.").format(get_nominee_display(n)),
				title=_("Invalid Nominee Percent"),
			)
		total += n.nominee_percent
	if abs(total - 100.0) > 0.01:
		frappe.throw(
			_("Total nominee percentage must be 100. Currently it is {}.").format(total),
			title=_("Invalid Nominee Percent"),
		)


def validate_nominee_minor_guardian(doc: Document) -> None:
	reference_date = doc.entry_date or today()
	guardian_names: set[str] = set()

	for n in doc.get("nominees") or []:
		if n.is_minor and not n.guardian:
			frappe.throw(
				_("Guardian is required for minor nominee {}.").format(get_nominee_display(n)),
				title=_("Guardian Required"),
			)
		if n.guardian:
			guardian_names.add(n.guardian)

	if not guardian_names:
		return

	guardians = frappe.db.get_all(
		DOCTYPE_INDIVIDUAL,
		filters={"name": ["in", list(guardian_names)]},
		fields=["name", "full_name", "date_of_birth"],
	)

	minor_guardian_names: set[str] = set()
	for g in guardians:
		if g.get("date_of_birth") and calculate_age(g["date_of_birth"], reference_date) < 18:
			minor_guardian_names.add(g["name"])

	for n in doc.get("nominees") or []:
		if n.guardian and n.guardian in minor_guardian_names:
			display = n.guardian_name_capture or n.guardian
			frappe.throw(
				_("Guardian {} for nominee {} is a minor. Guardian must be at least 18 years old.").format(
					display, get_nominee_display(n)
				),
				title=_("Invalid Guardian"),
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
