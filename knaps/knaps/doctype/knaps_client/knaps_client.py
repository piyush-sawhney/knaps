# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class KNAPSClient(Document):
	def validate(self):
		self.sync_client_pan_from_link()
		self.sync_client_name_from_link()
		self.validate_required_links()
		self.validate_pan_uniqueness()

	def sync_client_pan_from_link(self):
		"""Auto-fetch PAN from linked Person or Non Individual"""
		if self.investor_type in ["Individual", "Sole Proprietor"] and self.person:
			self.client_pan = frappe.db.get_value(
				"KNAPS Person", 
				self.person, 
				"pan"
			) or ""
		elif self.investor_type == "Non Individual" and self.non_individual:
			self.client_pan = frappe.db.get_value(
				"KNAPS Non Individual", 
				self.non_individual, 
				"pan"
			) or ""

	def sync_client_name_from_link(self):
		"""Auto-fetch client name from linked Person or Non Individual"""
		if self.investor_type == "Individual" and self.person:
			self.client_name = frappe.db.get_value(
				"KNAPS Person", 
				self.person, 
				"full_name"
			) or ""
		elif self.investor_type == "Non Individual" and self.non_individual:
			self.client_name = frappe.db.get_value(
				"KNAPS Non Individual", 
				self.non_individual, 
				"non_individual_name"
			) or ""
		# For Sole Proprietor: client_name is manually entered (no auto-fetch)

	def validate_required_links(self):
		"""Ensure correct link field is selected based on client type"""
		if self.investor_type in ["Individual", "Sole Proprietor"] and not self.person:
			frappe.throw(
				_("Person is required for Individual/Sole Proprietor"),
				title=_("Validation Error")
			)
		
		if self.investor_type == "Non Individual" and not self.non_individual:
			frappe.throw(
				_("Non Individual entity is required"),
				title=_("Validation Error")
			)

	def validate_pan_uniqueness(self):
		"""Validate PAN uniqueness based on investor type"""
		if not self.client_pan:
			return

		filters = {
			"client_pan": self.client_pan,
			"name": ["!=", self.name]
		}

		if self.investor_type == "Non Individual":
			filters["investor_type"] = "Non Individual"
		elif self.investor_type == "Individual":
			filters["investor_type"] = "Individual"
		elif self.investor_type == "Sole Proprietor":
			filters["investor_type"] = "Sole Proprietor"
			filters["client_name"] = self.client_name

		if frappe.db.exists("KNAPS Client", filters):
			frappe.throw(
				_("Client with this PAN already exists"),
				title=_("Duplicate PAN")
			)