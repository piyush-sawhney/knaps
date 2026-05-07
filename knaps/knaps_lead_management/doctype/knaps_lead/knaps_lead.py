# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.contacts.address_and_contact import (
	delete_contact_and_address,
	load_address_and_contact,
)
class KNAPSLead(Document):
	def onload(self):
		load_address_and_contact(self)

	def on_trash(self):
		delete_contact_and_address("Member", self.name)
		
	def validate(self):
		self.update_lead_name()

	def update_lead_name(self):
		"""Construct lead name from salutation, first, middle, and last name"""
		salutation = (self.salutation or "").strip()
		first = (self.first_name or "").strip()
		middle = (self.middle_name or "").strip()
		last = (self.last_name or "").strip()

		parts = [salutation, first, middle, last]
		self.lead_name = " ".join([part for part in parts if part])
