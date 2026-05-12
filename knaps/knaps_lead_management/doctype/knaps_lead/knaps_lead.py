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