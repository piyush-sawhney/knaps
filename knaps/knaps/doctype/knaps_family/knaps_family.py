# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KNAPSFamily(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_family_member.knaps_family_member import KNAPSFamilyMember

		family_name: DF.Data
		head_of_family: DF.Link
		members: DF.Table[KNAPSFamilyMember]
	# end: auto-generated types

	def on_trash(self):
		self._clear_family_if_matching("KNAPS Individual", self.head_of_family)
		for row in self.members or []:
			self._clear_family_if_matching(row.member_type, row.member_name)

	def validate(self):
		self._validate_unique_members()
		self._validate_head_not_listed_as_member()
		self._validate_no_deceased_members()
		self._validate_relation_with_head()
		self._validate_has_at_least_one_member()
		before_save = self.get_doc_before_save()
		self._assert_head_of_family_valid(before_save)
		self._assert_member_validity(before_save)

	def on_update(self):
		before_save = self.get_doc_before_save()
		self._update_head_of_family(before_save)
		self._sync_primary_members(before_save)

	def _validate_unique_members(self):
		seen = set()
		for row in self.members or []:
			key = (row.member_type, row.member_name)
			if key in seen:
				title = self._get_party_display_name(row.member_type, row.member_name)
				frappe.throw(_("{} is already added in {}.").format(title, self.family_name or self.name))
			seen.add(key)

	def _validate_head_not_listed_as_member(self):
		if not self.head_of_family:
			return
		for row in self.members or []:
			if row.member_type == "KNAPS Individual" and row.member_name == self.head_of_family:
				title = self._get_party_display_name("KNAPS Individual", self.head_of_family)
				frappe.throw(_("{} is the Head of Family and cannot be added as a member.").format(title))

	def _validate_relation_with_head(self):
		for row in self.members or []:
			if row.member_type == "KNAPS Individual" and not row.relation_with_head:
				title = self._get_party_display_name(row.member_type, row.member_name)
				frappe.throw(
					_("Relation with Head is mandatory for {} (an Individual member).").format(title)
				)
			if row.member_type == "KNAPS Non Individual" and row.relation_with_head:
				title = self._get_party_display_name(row.member_type, row.member_name)
				frappe.throw(
					_("Relation with Head is not applicable for {} (a Non Individual member).").format(title)
				)

	def _validate_has_at_least_one_member(self):
		if not self.members:
			frappe.throw(_("A family must have at least one member."))

	def _validate_no_deceased_members(self):
		if self.head_of_family:
			status = frappe.db.get_value("KNAPS Individual", self.head_of_family, "status")
			if status == "Deceased":
				title = self._get_party_display_name("KNAPS Individual", self.head_of_family)
				frappe.throw(
					_("{} is deceased and cannot be the Head of Family.").format(title),
					title=_("Deceased Individual"),
				)

		for row in self.members or []:
			if row.member_type == "KNAPS Individual":
				status = frappe.db.get_value("KNAPS Individual", row.member_name, "status")
				if status == "Deceased":
					title = self._get_party_display_name("KNAPS Individual", row.member_name)
					frappe.throw(_("{} is deceased and cannot be added as a member.").format(title))

	def _assert_head_of_family_valid(self, before_save):
		if not self.head_of_family:
			return

		previous_head = before_save.head_of_family if before_save else None
		if self.head_of_family == previous_head:
			return

		self._raise_if_primary_elsewhere("KNAPS Individual", self.head_of_family)

	def _assert_member_validity(self, before_save):
		old_primaries = set()
		if before_save:
			for row in before_save.members:
				if row.membership_type == "Primary":
					old_primaries.add((row.member_type, row.member_name))

		for row in self.members or []:
			key = (row.member_type, row.member_name)
			if row.membership_type == "Primary" and key not in old_primaries:
				if row.member_type in ("KNAPS Individual", "KNAPS Non Individual"):
					self._raise_if_primary_elsewhere(row.member_type, row.member_name)

	def _update_head_of_family(self, before_save):
		if not self.head_of_family:
			return

		previous_head = before_save.head_of_family if before_save else None
		if self.head_of_family == previous_head:
			return

		if previous_head:
			current = frappe.db.get_value("KNAPS Individual", previous_head, "family")
			if current == self.name:
				frappe.has_permission("KNAPS Individual", "write", previous_head, throw=True)
				frappe.db.set_value("KNAPS Individual", previous_head, "family", None)

		frappe.has_permission("KNAPS Individual", "write", self.head_of_family, throw=True)
		frappe.db.set_value("KNAPS Individual", self.head_of_family, "family", self.name)
		frappe.db.set_value("KNAPS Individual", self.head_of_family, "family_name", self.family_name)

	def _sync_primary_members(self, before_save):
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
				if row.member_type in ("KNAPS Individual", "KNAPS Non Individual"):
					frappe.has_permission(row.member_type, "write", row.member_name, throw=True)
					frappe.db.set_value(row.member_type, row.member_name, "family", self.name)
					frappe.db.set_value(row.member_type, row.member_name, "family_name", self.family_name)

			elif key in old_primaries:
				if not (row.member_type == "KNAPS Individual" and row.member_name == self.head_of_family):
					self._clear_family_if_matching(row.member_type, row.member_name)
				old_primaries.pop(key)

		for member_type, member_name in old_primaries:
			if not (member_type == "KNAPS Individual" and member_name == self.head_of_family):
				self._clear_family_if_matching(member_type, member_name)

	def _raise_if_primary_elsewhere(self, doctype, name):
		current_family = frappe.db.get_value(doctype, name, "family")
		if current_family and current_family != self.name:
			title = self._get_party_display_name(doctype, name)
			family_label = (
				frappe.db.get_value("KNAPS Family", current_family, "family_name") or current_family
			)
			frappe.throw(_("{} is already a primary member in {}.").format(title, family_label))

	def _clear_family_if_matching(self, doctype, name):
		if doctype not in ("KNAPS Individual", "KNAPS Non Individual"):
			return
		current = frappe.db.get_value(doctype, name, "family")
		if current == self.name:
			frappe.has_permission(doctype, "write", name, throw=True)
			frappe.db.set_value(doctype, name, "family", None)
			frappe.db.set_value(doctype, name, "family_name", None)

	def _get_party_display_name(self, doctype, name):
		if doctype == "KNAPS Individual":
			return frappe.db.get_value(doctype, name, "full_name") or name
		elif doctype == "KNAPS Non Individual":
			return frappe.db.get_value(doctype, name, "legal_name") or name
		return name
