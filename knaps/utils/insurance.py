from datetime import date

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, getdate

from knaps.utils.constants import DOCTYPE_CLIENT, DOCTYPE_INDIVIDUAL


def _init_holder_cache(doc: Document) -> None:
	cache: dict[str, date] = {}
	holder_names = [h.holder for h in doc.get("holders") or [] if h.holder]
	if not holder_names:
		doc._holder_cache = cache
		return

	clients = frappe.db.get_all(
		DOCTYPE_CLIENT,
		filters={"name": ["in", holder_names]},
		fields=["name", "individual"],
	)
	individual_names = [c["individual"] for c in clients if c.get("individual")]

	if individual_names:
		individuals = frappe.db.get_all(
			DOCTYPE_INDIVIDUAL,
			filters={"name": ["in", individual_names]},
			fields=["name", "date_of_birth"],
		)
		individual_dob = {i["name"]: i["date_of_birth"] for i in individuals}
		for c in clients:
			if c["individual"] and c["individual"] in individual_dob:
				cache[c["name"]] = individual_dob[c["individual"]]

	doc._holder_cache = cache


def set_insurance_member_date_of_birth(doc: Document) -> None:
	_init_holder_cache(doc)
	for h in doc.get("holders") or []:
		if h.holder and h.holder in doc._holder_cache:
			h.date_of_birth = doc._holder_cache[h.holder]


def set_primary_client(doc: Document) -> None:
	holders = doc.get("holders") or []
	primary_holders = [h for h in holders if h.is_primary]

	if not primary_holders:
		doc.primary_client = None
		doc.client_name = None
		return

	if len(primary_holders) > 1:
		frappe.throw(
			_("Only one member can be marked as primary."),
			title=_("Invalid Primary"),
		)

	primary = primary_holders[0]
	_validate_not_minor(primary)
	doc.primary_client = primary.holder
	client_name = frappe.db.get_value(DOCTYPE_CLIENT, primary.holder, "client_name")
	if client_name:
		doc.client_name = client_name


def _validate_not_minor(member) -> None:
	client = frappe.get_cached_doc(DOCTYPE_CLIENT, member.holder)
	if client.is_minor:
		display = frappe.db.get_value(DOCTYPE_CLIENT, member.holder, "client_name") or member.holder
		frappe.throw(
			_("{} is a minor and cannot be the primary member.").format(display),
			title=_("Minor Primary Member"),
		)


def set_maturity_date(doc: Document) -> None:
	if doc.start_date:
		doc.maturity_date = add_months(getdate(doc.start_date), doc.period_in_months)


def validate_premium_positive(doc: Document) -> None:
	if not doc.premium or doc.premium <= 0:
		frappe.throw(_("Premium must be positive."), title=_("Invalid Premium"))


def validate_start_date_before_maturity(doc: Document) -> None:
	if doc.start_date and doc.maturity_date:
		if getdate(doc.start_date) >= getdate(doc.maturity_date):
			frappe.throw(
				_("Start Date must be before Maturity Date."),
				title=_("Invalid Date Range"),
			)


def validate_status_requirements(doc: Document) -> None:
	if doc.status in ("Proposal", "Rejected"):
		if doc.policy_number:
			frappe.throw(
				_("Policy Number must be empty when status is {}.").format(doc.status),
				title=_("Invalid Status"),
			)
		if doc.policy_document:
			frappe.throw(
				_("Policy Document must be empty when status is {}.").format(doc.status),
				title=_("Invalid Status"),
			)

	elif doc.status in ("Active", "Renewed", "Surrendered"):
		if not doc.start_date:
			frappe.throw(
				_("Start Date is required when status is {}.").format(doc.status),
				title=_("Missing Start Date"),
			)
		if not doc.policy_number:
			frappe.throw(
				_("Policy Number is required when status is {}.").format(doc.status),
				title=_("Missing Policy Number"),
			)
		if not doc.policy_document:
			frappe.throw(
				_("Policy Document is required when status is {}.").format(doc.status),
				title=_("Missing Policy Document"),
			)


def warn_missing_nominees(doc: Document) -> None:
	if not doc.get("nominees") and not doc.is_existing_policy:
		frappe.msgprint(
			_("Consider adding nominees for this policy."),
			title=_("Nominees Recommended"),
			indicator="orange",
		)
