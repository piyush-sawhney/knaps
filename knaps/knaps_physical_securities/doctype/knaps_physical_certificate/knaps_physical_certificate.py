# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class KNAPSPhysicalCertificate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		certificate_number: DF.Data
		company_name_as_per_certificate: DF.Data | None
		distinctive_number_from: DF.Data
		distinctive_number_to: DF.Data
		face_value: DF.Int
		is_valid_certificate: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		quantity: DF.Int
	# end: auto-generated types

	def validate(self):
		if self.distinctive_number_from and self.distinctive_number_to:
			try:
				from_num = int(self.distinctive_number_from)
				to_num = int(self.distinctive_number_to)
			except ValueError:
				frappe.throw(_("Distinctive Number From and To must be valid numbers."))

			if from_num > to_num:
				frappe.throw(_("Distinctive Number From cannot be greater than Distinctive Number To."))

			self.quantity = to_num - from_num + 1