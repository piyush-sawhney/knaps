import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, getdate

from knaps.utils.constants import DOCTYPE_CLIENT


def set_primary_client(doc: Document) -> None:
	holders = doc.get("holders")
	if not holders:
		return

	first_holder = next((h for h in holders if h.order == "First"), None)
	if first_holder:
		doc.primary_client = first_holder.holder
		client_name = frappe.db.get_value(DOCTYPE_CLIENT, first_holder.holder, "client_name")
		if client_name:
			doc.client_name = client_name


def clear_maturity_if_no_start_date(doc: Document) -> None:
	if not doc.get("start_date"):
		doc.maturity_date = None
		if doc.get("extensions"):
			doc.set("extensions", [])


def set_maturity_date(doc: Document) -> None:
	if doc.get("extensions") and doc.extend_investment:
		extensions = doc.get("extensions")
		last_ext = extensions[-1]
		if last_ext.extension_date and last_ext.extension_period:
			doc.maturity_date = add_months(
				getdate(last_ext.extension_date),
				last_ext.extension_period,
			)
			return

	if doc.start_date:
		doc.maturity_date = add_months(
			getdate(doc.start_date),
			doc.period_in_months,
		)


def _resolve_holder_name(holder) -> str:
	doctype = getattr(holder, "holder_type", None) or DOCTYPE_CLIENT
	meta = frappe.get_meta(doctype)
	title_field = meta.get("title_field")
	if title_field:
		name = frappe.db.get_value(doctype, holder.holder, title_field)
		if name:
			return str(name)
	return holder.holder


def validate_unique_holders(doc: Document) -> None:
	seen: set[tuple[str, str]] = set()
	for holder in doc.get("holders"):
		key = (holder.holder, holder.order)
		if key in seen:
			frappe.throw(
				_("Holder {} with order '{}' appears more than once.").format(
					_resolve_holder_name(holder), holder.order
				),
				title=_("Duplicate Holder"),
			)
		seen.add(key)


def validate_minor_holder(doc: Document) -> None:
	for holder in doc.get("holders"):
		if holder.is_minor and holder.order != "First":
			frappe.throw(
				_("Minor holder {} can only be assigned as first holder.").format(
					_resolve_holder_name(holder)
				),
				title=_("Invalid Minor Holder"),
			)


def validate_holders_by_holding_type(doc: Document, enforce_single_for_non_individual: bool = False) -> None:
	holders = doc.get("holders")
	if not holders:
		return

	if enforce_single_for_non_individual:
		holder_names = [h.holder for h in holders]
		if holder_names:
			client_types = frappe.db.get_all(
				DOCTYPE_CLIENT,
				filters={"name": ["in", holder_names]},
				fields=["name", "client_type"],
			)
			non_individual_holders = [c for c in client_types if c.get("client_type") != "Individual"]
			if non_individual_holders and doc.holding_type != "Single":
				frappe.throw(
					_("Non-individual clients can only have Single holding type."),
					title=_("Invalid Holding Type"),
				)

	if doc.holding_type == "Single":
		_validate_single_holding_type(holders)
	else:
		_validate_nonsingle_holding_type(holders)


def _validate_single_holding_type(holders: list) -> None:
	first_count = sum(1 for h in holders if h.order == "First")
	guardian_count = sum(1 for h in holders if h.order == "Guardian")
	second_third_count = sum(1 for h in holders if h.order in ("Second", "Third"))

	if second_third_count > 0:
		frappe.throw(
			_("Single holding type does not allow additional holders."),
			title=_("Invalid Holder Order"),
		)

	if first_count != 1:
		frappe.throw(
			_("Single holding type requires exactly one first holder."),
			title=_("Invalid Holders"),
		)

	has_minor_first = any(h for h in holders if h.is_minor and h.order == "First")

	if has_minor_first:
		if guardian_count != 1:
			frappe.throw(
				_("A guardian holder is required when the first holder is a minor in Single holding type."),
				title=_("Guardian Required"),
			)
	elif guardian_count > 0:
		frappe.throw(
			_("Guardian holder is only allowed when the first holder is a minor in Single holding type."),
			title=_("Invalid Guardian"),
		)

	for h in holders:
		if h.order == "Guardian" and h.is_minor:
			frappe.throw(
				_("Guardian holder {} cannot be a minor.").format(_resolve_holder_name(h)),
				title=_("Invalid Guardian"),
			)


def _validate_nonsingle_holding_type(holders: list) -> None:
	guardian_count = sum(1 for h in holders if h.order == "Guardian")
	if guardian_count > 0:
		frappe.throw(
			_("Guardian holder is not allowed in non-single holding type."),
			title=_("Invalid Guardian"),
		)

	if len(holders) < 2:
		frappe.throw(
			_("Non-single holding type requires at least two holders."),
			title=_("Insufficient Holders"),
		)


def validate_nominees(doc: Document, nominees_optional_for_non_individual: bool = False) -> None:
	if nominees_optional_for_non_individual:
		holder_names = [h.holder for h in doc.get("holders") or []]
		if holder_names:
			client_types = frappe.db.get_all(
				DOCTYPE_CLIENT,
				filters={"name": ["in", holder_names]},
				fields=["name", "client_type"],
			)
			has_non_individual = any(c.client_type != "Individual" for c in client_types)
			if has_non_individual:
				if doc.get("nominees"):
					frappe.throw(
						_("Nominees are not allowed for non-individual clients."),
						title=_("Invalid Nominees"),
					)
				return

	if not doc.is_existing_investment and not doc.get("nominees"):
		frappe.throw(
			_("At least one nominee is required."),
			title=_("Nominees Required"),
		)


def validate_no_dates_for_entry_status(doc: Document) -> None:
	if doc.status not in ("Entry Done", "Submitted"):
		return

	if doc.start_date:
		frappe.throw(
			_("Start Date cannot be set when status is {}.").format(doc.status),
			title=_("Invalid Start Date"),
		)
	account_number = getattr(doc, "account_number", None)
	if account_number:
		frappe.throw(
			_("Account Number cannot be set when status is {}.").format(doc.status),
			title=_("Invalid Account Number"),
		)


def validate_account_number_for_active(doc: Document) -> None:
	if doc.status in ("Entry Done", "Submitted", "Rejected"):
		return
	account_number = getattr(doc, "account_number", None)
	if not account_number:
		frappe.throw(
			_("Account Number is required when status is {}.").format(doc.status),
			title=_("Missing Account Number"),
		)


def validate_start_date_with_account(doc: Document) -> None:
	if doc.status in ("Entry Done", "Submitted"):
		return
	account_number = getattr(doc, "account_number", None)
	if account_number and not doc.start_date:
		frappe.throw(
			_("Start Date is required when Account Number is provided."),
			title=_("Missing Start Date"),
		)


def validate_amount(doc: Document) -> None:
	if doc.amount <= 0:
		frappe.throw(_("Amount must be positive."), title=_("Invalid Amount"))


def validate_rate_of_interest(doc: Document) -> None:
	if doc.rate_of_interest <= 0:
		frappe.throw(_("Rate of Interest must be positive."), title=_("Invalid Rate"))
