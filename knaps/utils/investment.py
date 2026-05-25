import frappe
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.utils import add_months, getdate, today


def set_nominee_minor_status(doc) -> None:
	reference_date = doc.entry_date or today()
	for nominee in doc.get("nominees"):
		if nominee.nominee_date_of_birth:
			age = relativedelta(getdate(reference_date), getdate(nominee.nominee_date_of_birth)).years
			nominee.is_minor = 1 if age < 18 else 0


def set_primary_client(doc) -> None:
	holders = doc.get("holders")
	if not holders:
		return

	first_holder = next((h for h in holders if h.order == "First"), None)
	if first_holder:
		doc.primary_client = first_holder.holder
		client_name = frappe.db.get_value("KNAPS Client", first_holder.holder, "client_name")
		if client_name:
			doc.client_name = client_name


def set_maturity_date(doc) -> None:
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


def validate_unique_holders(doc) -> None:
	seen: set[tuple[str, str]] = set()
	for holder in doc.get("holders"):
		key = (holder.holder, holder.order)
		if key in seen:
			frappe.throw(
				_("Holder {} with order '{}' appears more than once.").format(holder.holder, holder.order),
				title=_("Duplicate Holder"),
			)
		seen.add(key)


def validate_minor_holder(doc) -> None:
	for holder in doc.get("holders"):
		if holder.is_minor and holder.order != "First":
			frappe.throw(
				_("Minor holder {} can only be assigned as first holder.").format(holder.holder),
				title=_("Invalid Minor Holder"),
			)


def validate_holders_by_holding_type(doc, enforce_single_for_non_individual: bool = False) -> None:
	holders = doc.get("holders")
	if not holders:
		return

	if enforce_single_for_non_individual:
		holder_names = [h.holder for h in holders]
		if holder_names:
			client_types = frappe.db.get_all(
				"KNAPS Client",
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
				_("Guardian holder {} cannot be a minor.").format(h.holder),
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


def build_nominee_name_cache(doc) -> dict[str, str]:
	nominees = doc.get("nominees")
	if not nominees:
		return {}
	names = [n.nominee_name for n in nominees if n.nominee_name]
	if not names:
		return {}
	records = frappe.db.get_all(
		"KNAPS Individual",
		filters={"name": ["in", names]},
		fields=["name", "full_name"],
	)
	return {r["name"]: r["full_name"] or r["name"] for r in records}


def get_nominee_display(doc, nominee) -> str:
	if not nominee.nominee_name:
		return ""
	cache: dict = getattr(doc, "_nominee_name_cache", {})
	return cache.get(nominee.nominee_name, nominee.nominee_name)


def validate_nominee_not_holder(doc) -> None:
	holders = doc.get("holders")
	nominees = doc.get("nominees")
	if not holders or not nominees:
		return

	holder_names = [h.holder for h in holders]
	client_data = frappe.db.get_all(
		"KNAPS Client",
		filters={"name": ["in", holder_names]},
		fields=["name", "individual"],
	)
	holder_individuals: set[str] = {c["individual"] for c in client_data if c["individual"]}

	for nominee in nominees:
		if nominee.nominee_name in holder_individuals:
			frappe.throw(
				_("Nominee {} cannot be a holder of this investment.").format(
					get_nominee_display(doc, nominee)
				),
				title=_("Invalid Nominee"),
			)


def validate_unique_nominees(doc) -> None:
	seen: set[str] = set()
	for nominee in doc.get("nominees"):
		if nominee.nominee_name in seen:
			frappe.throw(
				_("Nominee {} appears more than once.").format(get_nominee_display(doc, nominee)),
				title=_("Duplicate Nominee"),
			)
		seen.add(nominee.nominee_name)


def validate_nominee_percent_total(doc) -> None:
	nominees = doc.get("nominees")
	if not nominees:
		return

	total = 0
	for nominee in nominees:
		if not nominee.nominee_percent or nominee.nominee_percent <= 0:
			frappe.throw(
				_("Nominee {} must have a positive percentage.").format(get_nominee_display(doc, nominee)),
				title=_("Invalid Nominee Percent"),
			)
		total += nominee.nominee_percent

	if total != 100:
		frappe.throw(
			_("Total nominee percentage must be 100. Currently it is {}.").format(total),
			title=_("Invalid Nominee Percent"),
		)


def validate_nominee_minor_guardian(doc) -> None:
	for nominee in doc.get("nominees"):
		if nominee.is_minor and not nominee.guardian:
			frappe.throw(
				_("Guardian is required for minor nominee {}.").format(get_nominee_display(doc, nominee)),
				title=_("Guardian Required"),
			)


def validate_nominees(doc, nominees_optional_for_non_individual: bool = False) -> None:
	if nominees_optional_for_non_individual:
		holder_names = [h.holder for h in doc.get("holders") or []]
		if holder_names:
			client_types = frappe.db.get_all(
				"KNAPS Client",
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


def validate_payments(doc) -> None:
	if not doc.is_existing_investment and not doc.get("payments"):
		frappe.throw(
			_("At least one payment is required."),
			title=_("Payments Required"),
		)


def validate_entry_date_not_future(doc) -> None:
	if getdate(doc.entry_date) > getdate(today()):
		frappe.throw(
			_("Entry Date cannot be in the future."),
			title=_("Invalid Entry Date"),
		)


def validate_no_dates_for_entry_status(doc) -> None:
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


def validate_start_date_with_account(doc) -> None:
	if doc.status in ("Entry Done", "Submitted"):
		return
	account_number = getattr(doc, "account_number", None)
	if account_number and not doc.start_date:
		frappe.throw(
			_("Start Date is required when Account Number is provided."),
			title=_("Missing Start Date"),
		)


def validate_amount(doc) -> None:
	if doc.amount <= 0:
		frappe.throw(_("Amount must be positive."), title=_("Invalid Amount"))


def validate_rate_of_interest(doc) -> None:
	if doc.rate_of_interest <= 0:
		frappe.throw(_("Rate of Interest must be positive."), title=_("Invalid Rate"))


def validate_period_in_months(doc) -> None:
	if doc.period_in_months <= 0:
		frappe.throw(_("Period in months must be positive."), title=_("Invalid Period"))
