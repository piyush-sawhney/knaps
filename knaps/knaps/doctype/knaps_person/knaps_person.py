# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class KNAPSPerson(Document):
	def validate(self):
		"""Ensure full name is properly constructed from name components"""
		self.update_full_name()
	
	def update_full_name(self):
		"""Construct full name from first, middle, and last name"""
		# Trim whitespace from each component
		first = (self.first_name or "").strip()
		middle = (self.middle_name or "").strip()
		last = (self.last_name or "").strip()
		
		# Get old value for change detection (auditing)
		old_full_name = None
		if self.get_doc_before_save():
			old_full_name = self.get_doc_before_save().full_name
		
		# Construct full name with proper spacing
		parts = [first, middle, last]
		self.full_name = " ".join([part for part in parts if part])
		
		# Log when full name changes (for debugging/auditing)
		if old_full_name != self.full_name:
			frappe.logger().debug(
				f"Full name updated for {self.name or 'new record'}: "
				f"'{old_full_name}' -> '{self.full_name}'"
			)