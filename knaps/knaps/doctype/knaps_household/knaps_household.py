# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KNAPSHousehold(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_household_member.knaps_household_member import KNAPSHouseholdMember

		head_of_household: DF.Link
		household_name: DF.Data | None
		members: DF.Table[KNAPSHouseholdMember]
	# end: auto-generated types

	def on_trash(self):
		self._clear_primary_household_if_matching("KNAPS Person", self.head_of_household)
		for row in self.members or []:
			self._clear_primary_household_if_matching(row.member_type, row.member_name)

	def validate(self):
		self._validate_unique_members()
		self._validate_head_not_listed_as_member()
		self._validate_no_deceased_members()
		before_save = self.get_doc_before_save()
		self._update_head_of_household_primary_household(before_save)
		self._sync_primary_members_household(before_save)

	def _validate_unique_members(self):
		seen = set()
		for row in self.members or []:
			key = (row.member_type, row.member_name)
			if key in seen:
				title = self._get_party_display_name(row.member_type, row.member_name)
				frappe.throw(_("{} is already added in {}.").format(title, self.household_name or self.name))
			seen.add(key)

	def _validate_head_not_listed_as_member(self):
		if not self.head_of_household:
			return
		for row in self.members or []:
			if row.member_type == "KNAPS Person" and row.member_name == self.head_of_household:
				title = self._get_party_display_name("KNAPS Person", self.head_of_household)
				frappe.throw(_("{} is the Head of Household and cannot be added as a member.").format(title))

	def _validate_no_deceased_members(self):
		if self.head_of_household:
			status = frappe.db.get_value("KNAPS Person", self.head_of_household, "status")
			if status == "Deceased":
				title = self._get_party_display_name("KNAPS Person", self.head_of_household)
				frappe.throw(
					_("{} is deceased and cannot be the Head of Household.").format(title),
					title=_("Deceased Person"),
				)

		for row in self.members or []:
			if row.member_type == "KNAPS Person":
				status = frappe.db.get_value("KNAPS Person", row.member_name, "status")
				if status == "Deceased":
					title = self._get_party_display_name("KNAPS Person", row.member_name)
					frappe.throw(_("{} is deceased and cannot be added as a member.").format(title))

	def _update_head_of_household_primary_household(self, before_save):
		if not self.head_of_household:
			return

		previous_head = before_save.head_of_household if before_save else None
		if self.head_of_household == previous_head:
			return

		if previous_head:
			current = frappe.db.get_value("KNAPS Person", previous_head, "primary_household")
			if current == self.name:
				frappe.db.set_value("KNAPS Person", previous_head, "primary_household", None)

		self._raise_if_primary_elsewhere("KNAPS Person", self.head_of_household)
		frappe.db.set_value("KNAPS Person", self.head_of_household, "primary_household", self.name)

	def _sync_primary_members_household(self, before_save):
		old_primaries = {}
		if before_save:
			for row in before_save.members:
				if row.membership_type == "Primary":
					old_primaries[(row.member_type, row.member_name)] = row

		for row in self.members or []:
			key = (row.member_type, row.member_name)

			if row.membership_type == "Primary":
				if key in old_primaries:
					old_primaries.pop(key)
					continue
				if row.member_type in ("KNAPS Person", "KNAPS Non Individual"):
					self._raise_if_primary_elsewhere(row.member_type, row.member_name)
					frappe.db.set_value(row.member_type, row.member_name, "primary_household", self.name)

			elif key in old_primaries:
				if not (row.member_type == "KNAPS Person" and row.member_name == self.head_of_household):
					self._clear_primary_household_if_matching(row.member_type, row.member_name)
				old_primaries.pop(key)

		for member_type, member_name in old_primaries:
			if not (member_type == "KNAPS Person" and member_name == self.head_of_household):
				self._clear_primary_household_if_matching(member_type, member_name)

	def _raise_if_primary_elsewhere(self, doctype, name):
		current_hh = frappe.db.get_value(doctype, name, "primary_household")
		if current_hh and current_hh != self.name:
			title = self._get_party_display_name(doctype, name)
			hh_name = frappe.db.get_value("KNAPS Household", current_hh, "household_name") or current_hh
			frappe.throw(_("{} is already a primary member in {}.").format(title, hh_name))

	def _clear_primary_household_if_matching(self, doctype, name):
		if doctype not in ("KNAPS Person", "KNAPS Non Individual"):
			return
		current = frappe.db.get_value(doctype, name, "primary_household")
		if current == self.name:
			frappe.db.set_value(doctype, name, "primary_household", None)

	def _get_party_display_name(self, doctype, name):
		if doctype == "KNAPS Person":
			return frappe.db.get_value(doctype, name, "full_name") or name
		elif doctype == "KNAPS Non Individual":
			return frappe.db.get_value(doctype, name, "legal_name") or name
		return name
