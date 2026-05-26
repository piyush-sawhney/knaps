from datetime import date

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, getdate

from knaps.utils.constants import DOCTYPE_INDIVIDUAL


def _init_holder_cache(doc: Document) -> None:
	cache: dict[str, date] = {}
	holder_names = [h.holder for h in doc.get("holders") or [] if h.holder]
	if not holder_names:
		doc._holder_cache = cache
		return

	clients = frappe.db.get_all(
		"KNAPS Client",
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
	client_name = frappe.db.get_value("KNAPS Client", primary.holder, "client_name")
	if client_name:
		doc.client_name = client_name


def _validate_not_minor(member) -> None:
	client = frappe.get_cached_doc("KNAPS Client", member.holder)
	if client.is_minor:
		display = frappe.db.get_value("KNAPS Client", member.holder, "client_name") or member.holder
		frappe.throw(
			_("{} is a minor and cannot be the primary member.").format(display),
			title=_("Minor Primary Member"),
		)


def set_maturity_date(doc: Document) -> None:
	if doc.start_date:
		doc.maturity_date = add_months(getdate(doc.start_date), doc.period_in_months)


def set_maturity_date_general(doc: Document) -> None:
	if not doc.start_date:
		return
	start = getdate(doc.start_date)
	if doc.period_type == "Days":
		doc.maturity_date = add_days(start, doc.period)
	elif doc.period_type == "Months":
		doc.maturity_date = add_months(start, doc.period)
	elif doc.period_type == "Years":
		doc.maturity_date = add_months(start, doc.period * 12)


def set_title(doc: Document) -> None:
	if doc.client_name and doc.insurance_plan_name:
		doc.title = f"{doc.client_name} - {doc.insurance_plan_name}"
	elif doc.client_name:
		doc.title = f"{doc.client_name} - Health Insurance"


def validate_holders(doc: Document) -> None:
	holders = doc.get("holders") or []
	if not holders:
		frappe.throw(
			_("At least one member is required."),
			title=_("Members Required"),
		)

	seen_holders: set[str] = set()
	for h in holders:
		if h.holder in seen_holders:
			display = frappe.db.get_value("KNAPS Client", h.holder, "client_name") or h.holder
			frappe.throw(
				_("{} appears more than once in the members table.").format(display),
				title=_("Duplicate Member"),
			)
		seen_holders.add(h.holder)

	insured_count = sum(1 for h in holders if h.order == "Insured")

	if doc.policy_type == "Floater":
		if insured_count < 2:
			frappe.throw(
				_("Floater policy requires at least 2 members with role 'Insured'."),
				title=_("Insufficient Insured Members"),
			)
	elif doc.policy_type == "Multi-Individual":
		if insured_count < 1:
			frappe.throw(
				_("Multi-Individual policy requires at least 1 member with role 'Insured'."),
				title=_("Insufficient Insured Members"),
			)


def validate_holder_sum_insured(doc: Document) -> None:
	holders = doc.get("holders") or []
	if doc.policy_type == "Floater":
		for h in holders:
			if h.sum_insured and h.sum_insured > 0:
				display = frappe.db.get_value("KNAPS Client", h.holder, "client_name") or h.holder
				frappe.throw(
					_(
						"Member {} should not have a sum insured in a Floater policy. Use the policy-level Floater Sum Insured instead."
					).format(display),
					title=_("Invalid Member Sum Insured"),
				)
	elif doc.policy_type == "Multi-Individual":
		for h in holders:
			if h.order != "Insured":
				continue
			if not h.sum_insured or h.sum_insured <= 0:
				display = frappe.db.get_value("KNAPS Client", h.holder, "client_name") or h.holder
				frappe.throw(
					_("Insured member {} requires a sum insured in a Multi-Individual policy.").format(
						display
					),
					title=_("Missing Member Sum Insured"),
				)


def validate_floater_sum_insured(doc: Document) -> None:
	if doc.policy_type == "Floater":
		if not doc.floater_sum_insured or doc.floater_sum_insured <= 0:
			frappe.throw(
				_("Floater Sum Insured is required and must be positive for Floater policies."),
				title=_("Invalid Floater Sum Insured"),
			)
	elif doc.policy_type == "Multi-Individual":
		if doc.floater_sum_insured and doc.floater_sum_insured > 0:
			frappe.throw(
				_("Floater Sum Insured should not be set for Multi-Individual policies."),
				title=_("Invalid Floater Sum Insured"),
			)


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
