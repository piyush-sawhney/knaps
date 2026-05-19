# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KNAPSBank(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		bank_account_number: DF.Data
		bank_branch: DF.Data | None
		bank_name: DF.Data
		first_holder: DF.DynamicLink
		first_holder_name: DF.Data | None
		holder_type: DF.Link
		holding_type: DF.Link | None
		ifsc: DF.Data
		name: DF.Int | None
		second_holder: DF.Link | None
		second_holder_name: DF.Data | None
		title: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self._validate_ifsc()
		self._validate_second_holder()
		self._populate_holder_names()

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

	def _validate_second_holder(self):
		if not self.second_holder:
			return
		if self.holder_type != "KNAPS Person":
			frappe.throw(_("Second holder can only be set when the holder is an Individual."))
		if self.holding_type == "Single":
			frappe.throw(_("Second holder cannot be set when holding type is Single."))
		if self.second_holder == self.first_holder:
			frappe.throw(_("First holder and second holder cannot be the same."))

	def _populate_holder_names(self):
		if self.first_holder and self.holder_type:
			name_field = "full_name" if self.holder_type == "KNAPS Person" else "legal_name"
			name = frappe.db.get_value(self.holder_type, self.first_holder, name_field)
			self.first_holder_name = name or self.first_holder
		else:
			self.first_holder_name = None
		if self.second_holder:
			second_name = frappe.db.get_value("KNAPS Person", self.second_holder, "full_name")
			self.second_holder_name = second_name or self.second_holder
		else:
			self.second_holder_name = None
		self._compute_title()

	def _compute_title(self):
		holder = self.first_holder_name or ""
		last4 = (self.bank_account_number or "")[-4:] if self.bank_account_number else ""
		if holder and last4:
			self.title = f"{holder} - {last4}"
		elif holder:
			self.title = holder
		elif last4:
			self.title = last4
		else:
			self.title = None
