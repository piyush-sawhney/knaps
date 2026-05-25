from datetime import date

import frappe
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, formatdate, getdate, today


class KNAPSPOInvestment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_payment.knaps_payment import KNAPSPayment
		from knaps.knaps_client_management.doctype.knaps_holder.knaps_holder import KNAPSHolder
		from knaps.knaps_client_management.doctype.knaps_nominee.knaps_nominee import KNAPSNominee
		from knaps.knaps_po.doctype.knaps_po_extension.knaps_po_extension import KNAPSPOExtension

		account_number: DF.Data | None
		amount: DF.Currency
		client_name: DF.Data | None
		currency: DF.Link | None
		entry_date: DF.Date
		extend_investment: DF.Check
		extensions: DF.Table[KNAPSPOExtension]
		holders: DF.Table[KNAPSHolder]
		holding_type: DF.Link
		is_existing_investment: DF.Check
		maturity_date: DF.Date | None
		nominees: DF.Table[KNAPSNominee]
		partner: DF.Link | None
		passbook_status: DF.Literal["Not Created", "With Us", "With Client", "With PO"]
		payments: DF.Table[KNAPSPayment]
		period_in_months: DF.Int
		po_branch: DF.Data | None
		primary_client: DF.Link | None
		rate_of_interest: DF.Float
		scheme_code: DF.Data | None
		scheme_name: DF.Link
		start_date: DF.Date | None
		status: DF.Literal[
			"Entry Done",
			"Submitted",
			"Active",
			"Renewed",
			"Matured",
			"Pre-Matured",
			"Transmitted",
			"Rejected",
		]
		through_partner: DF.Check
		through_us: DF.Check
		title: DF.Data | None
	# end: auto-generated types

	def autoname(self) -> None:
		entry_date = self.entry_date or date.today()
		if isinstance(entry_date, str):
			entry_date = getdate(entry_date)

		if entry_date.month >= 4:
			ty_start = entry_date.year
			ty_end = entry_date.year + 1
		else:
			ty_start = entry_date.year - 1
			ty_end = entry_date.year

		prefix = f"KNAPS-PO-{ty_start % 100:02d}-{ty_end % 100:02d}-"

		last_serial = 0
		last = frappe.db.get_value(
			"KNAPS PO Investment",
			{"name": ["like", f"{prefix}%"]},
			"name",
			order_by="name desc",
		)
		if last:
			last_serial = int(last.split("-")[-1])

		self.name = f"{prefix}{last_serial + 1:08d}"

	def before_validate(self) -> None:
		self._set_nominee_minor_status()

	def before_save(self) -> None:
		self._set_primary_client()
		self._set_title()
		self._set_maturity_date()

	def validate(self) -> None:
		self._nominee_name_cache = self._build_nominee_name_cache()
		self._validate_unique_holders()
		self._validate_minor_holder()
		self._validate_holders_by_holding_type()
		self._validate_nominee_not_holder()
		self._validate_unique_nominees()
		self._validate_nominee_percent_total()
		self._validate_nominee_minor_guardian()
		self._validate_nominees()
		self._validate_payments()
		self._validate_entry_date_not_future()
		self._validate_no_dates_for_entry_status()
		self._validate_start_date_with_account()
		self._validate_amount()
		self._validate_rate_of_interest()
		self._validate_period_in_months()
		self._validate_extension_sequence()

	def _set_title(self) -> None:
		if self.client_name and self.scheme_code:
			self.title = f"{self.client_name} - {self.scheme_code}"

	def _set_primary_client(self) -> None:
		holders = self.get("holders")
		if not holders:
			return

		first_holder = next((h for h in holders if h.order == "First"), None)
		if first_holder:
			self.primary_client = first_holder.holder
			client_name = frappe.db.get_value("KNAPS Client", first_holder.holder, "client_name")
			if client_name:
				self.client_name = client_name

	def _set_maturity_date(self) -> None:
		if self.extend_investment and self.get("extensions"):
			extensions = self.get("extensions")
			last_ext = extensions[-1]
			if last_ext.extension_date and last_ext.extension_period:
				self.maturity_date = add_months(
					getdate(last_ext.extension_date),
					last_ext.extension_period,
				)
		elif self.start_date:
			self.maturity_date = add_months(
				getdate(self.start_date),
				self.period_in_months,
			)

	def _validate_unique_holders(self) -> None:
		seen: set[tuple[str, str]] = set()
		for holder in self.get("holders"):
			key = (holder.holder, holder.order)
			if key in seen:
				frappe.throw(
					_("Holder {} with order '{}' appears more than once.").format(
						holder.holder, holder.order
					),
					title=_("Duplicate Holder"),
				)
			seen.add(key)

	def _validate_minor_holder(self) -> None:
		for holder in self.get("holders"):
			if holder.is_minor and holder.order != "First":
				frappe.throw(
					_("Minor holder {} can only have order 'First'.").format(holder.holder),
					title=_("Invalid Minor Holder"),
				)

	def _validate_minor_guardian(self) -> None:
		has_minor_first = any(h for h in self.get("holders") if h.is_minor and h.order == "First")
		has_guardian = any(h for h in self.get("holders") if h.order == "Guardian")
		if has_minor_first and not has_guardian:
			frappe.throw(
				_("A Guardian holder is required when the first holder is a minor."),
				title=_("Guardian Required"),
			)

	def _validate_holders_by_holding_type(self) -> None:
		holders = self.get("holders")
		if not holders:
			return

		if self.holding_type == "Single":
			self._validate_single_holding_type(holders)
		else:
			self._validate_nonsingle_holding_type(holders)

	def _validate_single_holding_type(self, holders: list) -> None:
		first_count = sum(1 for h in holders if h.order == "First")
		guardian_count = sum(1 for h in holders if h.order == "Guardian")
		second_third_count = sum(1 for h in holders if h.order in ("Second", "Third"))

		if second_third_count > 0:
			frappe.throw(
				_("Single holding type cannot have holders with order 'Second' or 'Third'."),
				title=_("Invalid Holder Order"),
			)

		if first_count != 1:
			frappe.throw(
				_("Single holding type must have exactly one holder with order 'First'."),
				title=_("Invalid Holders"),
			)

		has_minor_first = any(h for h in holders if h.is_minor and h.order == "First")

		if has_minor_first:
			if guardian_count != 1:
				frappe.throw(
					_(
						"A Guardian holder is required when the first holder in a Single holding type is a minor."
					),
					title=_("Guardian Required"),
				)
		elif guardian_count > 0:
			frappe.throw(
				_("Guardian holder is only allowed when the first holder is a minor."),
				title=_("Invalid Guardian"),
			)

		for h in holders:
			if h.order == "Guardian" and h.is_minor:
				frappe.throw(
					_("Guardian holder {} cannot be a minor.").format(h.holder),
					title=_("Invalid Guardian"),
				)

	def _validate_nonsingle_holding_type(self, holders: list) -> None:
		guardian_count = sum(1 for h in holders if h.order == "Guardian")
		if guardian_count > 0:
			frappe.throw(
				_("Guardian holder is only allowed for Single holding type with a minor first holder."),
				title=_("Invalid Guardian"),
			)

		if len(holders) < 2:
			frappe.throw(
				_("Non-single holding type requires at least 2 holders."),
				title=_("Insufficient Holders"),
			)

	def _get_nominee_display(self, nominee) -> str:
		if not nominee.nominee_name:
			return ""
		return self._nominee_name_cache.get(nominee.nominee_name, nominee.nominee_name)

	def _build_nominee_name_cache(self) -> dict[str, str]:
		nominees = self.get("nominees")
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

	def _set_nominee_minor_status(self) -> None:
		reference_date = self.entry_date or today()
		for nominee in self.get("nominees"):
			if nominee.nominee_date_of_birth:
				age = relativedelta(getdate(reference_date), getdate(nominee.nominee_date_of_birth)).years
				nominee.is_minor = 1 if age < 18 else 0

	def _validate_nominee_not_holder(self) -> None:
		holders = self.get("holders")
		nominees = self.get("nominees")
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
						self._get_nominee_display(nominee)
					),
					title=_("Invalid Nominee"),
				)

	def _validate_unique_nominees(self) -> None:
		seen: set[str] = set()
		for nominee in self.get("nominees"):
			if nominee.nominee_name in seen:
				frappe.throw(
					_("Nominee {} appears more than once.").format(self._get_nominee_display(nominee)),
					title=_("Duplicate Nominee"),
				)
			seen.add(nominee.nominee_name)

	def _validate_nominee_percent_total(self) -> None:
		nominees = self.get("nominees")
		if not nominees:
			return

		total = 0
		for nominee in nominees:
			if not nominee.nominee_percent or nominee.nominee_percent <= 0:
				frappe.throw(
					_("Nominee {} must have a positive percentage.").format(
						self._get_nominee_display(nominee)
					),
					title=_("Invalid Nominee Percent"),
				)
			total += nominee.nominee_percent

		if total != 100:
			frappe.throw(
				_("Total nominee percentage must be 100. Currently it is {}.").format(total),
				title=_("Invalid Nominee Percent"),
			)

	def _validate_nominee_minor_guardian(self) -> None:
		for nominee in self.get("nominees"):
			if nominee.is_minor and not nominee.guardian:
				frappe.throw(
					_("Guardian is required for minor nominee {}.").format(
						self._get_nominee_display(nominee)
					),
					title=_("Guardian Required"),
				)

	def _validate_nominees(self) -> None:
		if not self.is_existing_investment and not self.get("nominees"):
			frappe.throw(
				_("At least one nominee is required."),
				title=_("Nominees Required"),
			)

	def _validate_payments(self) -> None:
		if not self.is_existing_investment and not self.get("payments"):
			frappe.throw(
				_("At least one payment is required."),
				title=_("Payments Required"),
			)

	def _validate_no_dates_for_entry_status(self) -> None:
		if self.status not in ("Entry Done", "Submitted"):
			return

		if self.start_date:
			frappe.throw(
				_("Start Date cannot be set when status is {}.").format(self.status),
				title=_("Invalid Start Date"),
			)
		if self.account_number:
			frappe.throw(
				_("Account Number cannot be set when status is {}.").format(self.status),
				title=_("Invalid Account Number"),
			)

	def _validate_start_date_with_account(self) -> None:
		if self.status in ("Entry Done", "Submitted"):
			return
		if self.account_number and not self.start_date:
			frappe.throw(
				_("Start Date is required when Account Number is provided."),
				title=_("Missing Start Date"),
			)

	def _validate_amount(self) -> None:
		if self.amount <= 0:
			frappe.throw(_("Amount must be positive."), title=_("Invalid Amount"))

	def _validate_rate_of_interest(self) -> None:
		if self.rate_of_interest <= 0:
			frappe.throw(_("Rate of Interest must be positive."), title=_("Invalid Rate"))

	def _validate_period_in_months(self) -> None:
		if self.period_in_months <= 0:
			frappe.throw(_("Period in months must be positive."), title=_("Invalid Period"))

	def _validate_entry_date_not_future(self) -> None:
		if getdate(self.entry_date) > getdate(today()):
			frappe.throw(
				_("Entry Date cannot be in the future."),
				title=_("Invalid Entry Date"),
			)

	def _validate_extension_sequence(self) -> None:
		extensions = self.get("extensions")
		if not extensions:
			return

		if not self.extend_investment:
			frappe.throw(
				_("Extensions can only be added when Extend Investment is checked."),
				title=_("Invalid Extension"),
			)

		if not self.start_date:
			return

		original_maturity = add_months(getdate(self.start_date), self.period_in_months)

		for i, ext in enumerate(extensions):
			ext_num = ext.idx

			if ext.extension_period <= 0:
				frappe.throw(
					_("Extension #{}: Extension period must be positive.").format(ext_num),
					title=_("Invalid Extension Period"),
				)

			if i == 0:
				if getdate(ext.extension_date) < getdate(original_maturity):
					frappe.throw(
						_("Extension #{}: Date must be on or after the maturity date {}.").format(
							ext_num, formatdate(original_maturity, "dd-mm-yyyy")
						),
						title=_("Invalid Extension Date"),
					)
			else:
				prev = extensions[i - 1]
				prev_maturity = add_months(getdate(prev.extension_date), prev.extension_period)
				if getdate(ext.extension_date) < getdate(prev_maturity):
					frappe.throw(
						_("Extension #{}: Date must be on or after the previous maturity date {}.").format(
							ext_num, formatdate(prev_maturity, "dd-mm-yyyy")
						),
						title=_("Invalid Extension Date"),
					)
