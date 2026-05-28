# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from knaps.utils.constants import DOCTYPE_INDIVIDUAL, DOCTYPE_NON_INDIVIDUAL
from knaps.utils.investment import (
	validate_holders_by_holding_type,
	validate_minor_holder,
	validate_unique_holders,
)
from knaps.utils.shared import calculate_age


class KNAPSBank(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_bank_holder.knaps_bank_holder import KNAPSBankHolder

		account_number: DF.Data
		account_type: DF.Literal["", "Saving", "Current", "NRO", "NRE", "FCNR"]
		bank_name: DF.Data
		branch: DF.Data | None
		holder_type: DF.Link | None
		holders: DF.Table[KNAPSBankHolder]
		holding_type: DF.Link | None
		ifsc: DF.Data
		is_active: DF.Check
		is_name_same: DF.Check
		name: DF.Int | None
		primary_holder: DF.DynamicLink | None
		primary_holder_name: DF.Data | None
		title: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self._validate_ifsc()
		self._populate_minor_status()
		self._validate_holders()
		self._set_primary_holder()
		self._validate_primary_holder()

	def before_save(self):
		self._compute_title()

	def _validate_ifsc(self):
		if not self.ifsc:
			return
		import re

		if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", self.ifsc):
			frappe.throw(
				_(
					"IFSC must be 11 characters: first 4 letters, then 0, then 6 alphanumeric characters. Example: HDFC0001234."
				)
			)

	def _populate_minor_status(self):
		for h in self.holders:
			if h.holder_type == DOCTYPE_INDIVIDUAL:
				dob = frappe.db.get_value(DOCTYPE_INDIVIDUAL, h.holder, "date_of_birth")
				h.is_minor = 1 if dob and calculate_age(dob) < 18 else 0
			else:
				h.is_minor = 0

	def _check_duplicate_orders(self):
		seen: set[str] = set()
		for h in self.holders:
			if h.order and h.order in seen:
				frappe.throw(
					_("Order '{}' appears more than once.").format(h.order),
					title=_("Duplicate Order"),
				)
			seen.add(h.order)

	def _validate_holders(self):
		if not self.holders:
			frappe.throw(_("At least one holder is required."), title=_("Invalid Holders"))

		validate_unique_holders(self)
		self._check_duplicate_orders()
		self._check_duplicate_holders_across_orders()

		has_non_individual = any(h.holder_type == DOCTYPE_NON_INDIVIDUAL for h in self.holders)
		has_individual = any(h.holder_type == DOCTYPE_INDIVIDUAL for h in self.holders)

		if has_non_individual and has_individual:
			frappe.throw(
				_("Individual and Non Individual holders cannot be mixed in the same bank account."),
				title=_("Mixed Holder Types"),
			)

		if has_non_individual:
			self._validate_non_individual_holders()
		else:
			validate_minor_holder(self)
			validate_holders_by_holding_type(self)

	def _check_duplicate_holders_across_orders(self):
		seen: set[str] = set()
		for h in self.holders:
			if h.holder in seen:
				display = self._get_holder_display_name(h)
				frappe.throw(
					_("Holder '{}' appears more than once.").format(display),
					title=_("Duplicate Holder"),
				)
			seen.add(h.holder)

	def _get_holder_display_name(self, holder) -> str:
		if holder.holder_type == DOCTYPE_INDIVIDUAL:
			name = frappe.db.get_value(DOCTYPE_INDIVIDUAL, holder.holder, "full_name")
		elif holder.holder_type == DOCTYPE_NON_INDIVIDUAL:
			name = frappe.db.get_value(DOCTYPE_NON_INDIVIDUAL, holder.holder, "legal_name")
		else:
			name = None
		return name or holder.holder

	def _validate_non_individual_holders(self):
		if len(self.holders) != 1 or self.holders[0].order != "First":
			frappe.throw(
				_("Non Individual holding requires exactly one first holder."),
				title=_("Invalid Holders"),
			)
		if self.holding_type != "Single":
			frappe.throw(
				_("Non Individual holders can only have Single holding type."),
				title=_("Invalid Holding Type"),
			)
		if self.account_type == "Saving":
			frappe.msgprint(
				_(
					"This is a Non Individual bank account with Saving account type. Please confirm this is correct."
				),
				indicator="orange",
			)

	def _set_primary_holder(self):
		first = next((h for h in self.holders if h.order == "First"), None)
		if not first:
			return
		self.holder_type = first.holder_type
		self.primary_holder = first.holder
		if self.is_name_same:
			name_field = "full_name" if first.holder_type == DOCTYPE_INDIVIDUAL else "legal_name"
			name = frappe.db.get_value(first.holder_type, first.holder, name_field)
			self.primary_holder_name = name
		if not any(h.is_primary for h in self.holders):
			first.is_primary = 1

	def _validate_primary_holder(self):
		primary_count = sum(1 for h in self.holders if h.is_primary)
		if primary_count == 0:
			frappe.throw(
				_("At least one holder must be marked as primary."),
				title=_("Missing Primary Holder"),
			)
		if primary_count > 1:
			frappe.throw(
				_("Only one holder can be marked as primary."),
				title=_("Multiple Primary Holders"),
			)

	def _compute_title(self):
		holder = self.primary_holder_name or ""
		last4 = (self.account_number or "")[-4:] if self.account_number else ""
		if holder and last4:
			self.title = f"{holder} - {last4}"
		elif holder:
			self.title = holder
		elif last4:
			self.title = last4
		else:
			self.title = None
